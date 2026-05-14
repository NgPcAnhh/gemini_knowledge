import asyncio
import json
import logging
import os
import redis.asyncio as redis
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from state import state
from services import process_event_update, compute_realtime_snapshot

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("f88-realtime-api")

app = FastAPI(title="Finnova Real-time API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()

@app.post("/api/recompute")
async def recompute_snapshot():
    async with state.lock:
        state.data = await asyncio.to_thread(compute_realtime_snapshot)
        state.reset_seen_events()
    return state.data


@app.get("/api/snapshot")
async def get_snapshot():
    # Return current state (if empty, it will be initialized by the first websocket or event)
    if not state.data.get("active_date"):
        state.data = await asyncio.to_thread(compute_realtime_snapshot)
    return state.data

@app.websocket("/ws/realtime")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    # Send initial snapshot immediately on connect
    if not state.data.get("active_date"):
        state.data = await asyncio.to_thread(compute_realtime_snapshot)
    await websocket.send_json(state.data)
    
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def redis_listener():
    r = redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        db=int(os.getenv("REDIS_DB", "0")),
        decode_responses=True
    )
    pubsub = r.pubsub()
    await pubsub.subscribe(os.getenv("REDIS_CHANNEL", "f88_realtime"))
    
    logger.info("Redis Listener started, subscribed to f88_realtime")
    
    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message:
                updated_data = await process_event_update(message["data"])
                await manager.broadcast(updated_data)
            await asyncio.sleep(0.01)
    except Exception as e:
        logger.error(f"Redis Listener error: {e}")
    finally:
        await pubsub.unsubscribe()
        await r.close()

@app.on_event("startup")
async def startup_event():
    # Pre-initialize state
    state.data = await asyncio.to_thread(compute_realtime_snapshot)
    asyncio.create_task(redis_listener())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
