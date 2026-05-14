// js/realtime/map.js

function initVietnamMap() {
    const mapEl = document.getElementById('vnMap');
    if (!mapEl || typeof L === 'undefined') return;

    if (window._vnMap) {
        try { window._vnMap.remove(); } catch (_) {}
        window._vnMap = null;
        window._vnMarkers = {};
        window._vnMarkerPrev = {};
    }

    const vnBounds = L.latLngBounds([8.5, 102.0], [23.5, 109.5]);
    const map = L.map('vnMap', { 
        renderer: L.canvas({ padding: 0.5 }), // Use Canvas renderer for 60 FPS performance
        zoomControl: true, 
        attributionControl: false, 
        minZoom: 5, 
        maxZoom: 13 
    });
    map.fitBounds(vnBounds);
    window._vnMap = map;
    window._vnMarkers = {};
    window._vnMarkerPrev = {};

    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png', { maxZoom: 19 }).addTo(map);

    fetch('https://raw.githubusercontent.com/TungTh/tungth.github.io/master/data/vietnam.geojson')
        .then(r => r.json())
        .then(data => {
            if (!window._vnMap) return;
            window._vnGeoLayer = L.geoJSON(data, {
                style: { color: '#00a651', weight: 1, opacity: 0.3, fillColor: '#00a651', fillOpacity: 0.02 }
            }).addTo(map);
        })
        .catch(() => console.warn('GeoJSON load failed'));

    setTimeout(() => { if (window._vnMap) window._vnMap.invalidateSize(); }, 300);
    if (window.latestRealtimePayload && Array.isArray(window.latestRealtimePayload.map)) updateVietnamMap(window.latestRealtimePayload.map);
}

// Throttling logic for 60 FPS
window._vnMapUpdateRequested = false;
window._vnMapPendingData = null;

function updateVietnamMap(mapItems) {
    window._vnMapPendingData = mapItems;
    if (!window._vnMapUpdateRequested) {
        window._vnMapUpdateRequested = true;
        requestAnimationFrame(processVietnamMapUpdate);
    }
}

function pulseCircleMarker(marker, baseRadius) {
    const base = Number(baseRadius) || 5;
    let frame = 0;
    const totalFrames = 10;
    const step = () => {
        frame += 1;
        const t = frame / totalFrames;
        const scale = 1 + 0.25 * Math.sin(t * Math.PI);
        marker.setRadius(base * scale);
        if (frame < totalFrames) {
            requestAnimationFrame(step);
        } else {
            marker.setRadius(base);
        }
    };
    requestAnimationFrame(step);
}

function processVietnamMapUpdate() {
    window._vnMapUpdateRequested = false;
    const mapItems = window._vnMapPendingData;
    if (!window._vnMap || !Array.isArray(mapItems)) return;

    if (!window._vnMarkerPrev) window._vnMarkerPrev = {};

    mapItems.forEach(item => {
        const lat = Number(item.lat);
        const lng = Number(item.lng);
        if (!Number.isFinite(lat) || !Number.isFinite(lng)) return;

        const key = String(item.key || `${lat},${lng}`);
        const color = item.risk_level === 'high' ? '#ef4444' : (item.risk_level === 'medium' ? '#f59e0b' : '#00a651');
        let marker = window._vnMarkers[key];
        const radius = 5;

        const hadPrev = Object.prototype.hasOwnProperty.call(window._vnMarkerPrev, key);
        const prev = window._vnMarkerPrev[key] || { loans: 0, disb_amt: 0, coll_amt: 0 };
        const loans = Number(item.loans || 0);
        const disb = Number(item.disb_amt || 0);
        const coll = Number(item.coll_amt || 0);
        const activityChanged = prev.loans !== loans || prev.disb_amt !== disb || prev.coll_amt !== coll;
        window._vnMarkerPrev[key] = { loans, disb_amt: disb, coll_amt: coll };

        if (!marker) {
            marker = L.circleMarker([lat, lng], { 
                radius, 
                fillColor: color, 
                color, 
                weight: 2, 
                opacity: 0.9, 
                fillOpacity: 0.65 
            }).addTo(window._vnMap);
            window._vnMarkers[key] = marker;
        } else {
            const currentLatLng = marker.getLatLng();
            if (currentLatLng.lat !== lat || currentLatLng.lng !== lng) {
                marker.setLatLng([lat, lng]);
            }
            if (marker.getRadius() !== radius) {
                marker.setRadius(radius);
            }
            if (marker.options.fillColor !== color) {
                marker.setStyle({ color, fillColor: color });
            }
        }

        if (hadPrev && activityChanged) {
            pulseCircleMarker(marker, radius);
        }

        const lateCt = Number(item.late_contracts_today || 0);
        const lateLabel = lateCt > 5 ? 'Cao (đỏ)' : lateCt >= 1 ? 'Trung bình (vàng)' : 'Thấp (xanh)';

        const tooltipHTML = `
            <div style="font-family: 'Inter', sans-serif; padding: 5px;">
                <div style="font-weight: 800; color: #fff; margin-bottom: 5px; border-bottom: 1px solid rgba(255,255,255,0.2); padding-bottom: 3px;">
                    ${item.name}
                </div>
                <div style="font-size: 11px; color: #ccc;">
                    <div>HĐ giải ngân hôm nay: <span style="color: #fff; font-weight: bold;">${item.loans}</span></div>
                    <div>Số tiền GN: <span style="color: #00a651; font-weight: bold;">${(Number(item.disb_amt || 0) / 1_000_000).toFixed(1)}M</span></div>
                    <div>Số tiền Thu: <span style="color: #3b82f6; font-weight: bold;">${(Number(item.coll_amt || 0) / 1_000_000).toFixed(1)}M</span></div>
                    <div>HĐ trả chậm / rủi ro (trong ngày): <span style="color: #fbbf24; font-weight: bold;">${lateCt}</span></div>
                    <div style="margin-top: 5px; padding-top: 3px; border-top: 1px dashed rgba(255,255,255,0.1); color: rgba(255,255,255,0.55);">
                        <i class="fas fa-layer-group"></i> Mức rủi ro (theo trả chậm): <strong>${lateLabel}</strong>
                    </div>
                </div>
            </div>
        `;

        if (!marker.getTooltip()) {
            marker.bindTooltip(tooltipHTML, { 
                className: 'leaflet-tooltip-custom', 
                direction: 'top', 
                offset: [0, -5] 
            });
        } else {
            if (marker.getTooltip().getContent() !== tooltipHTML) {
                marker.setTooltipContent(tooltipHTML);
            }
        }
    });
}
