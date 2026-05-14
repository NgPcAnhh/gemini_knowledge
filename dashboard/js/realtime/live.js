// js/realtime/live.js

(function () {
    const defaultApiBase = (() => {
        if (window.F88_API_BASE) return window.F88_API_BASE;
        return `${window.location.protocol}//${window.location.hostname}:8000`;
    })();

    const API_BASE = defaultApiBase.replace(/\/$/, '');
    const WS_BASE = API_BASE.replace(/^http/, 'ws');

    let socket = null;
    let socketStarted = false;
    let reconnectTimer = null;
    let currentFeedFilter = 'all';
    let lastFeedData = [];
    /** Tránh renderFeed() khi mảng feed không đổi nội dung. */
    let lastFeedContentSignature = null;
    /** Feed mới nhất từ API/WS; UI stream chỉ đồng bộ tối đa mỗi FEED_UI_MIN_MS. */
    let pendingFeedItems = null;
    let lastFeedUiAt = 0;
    let feedUiIntervalId = null;
    const FEED_UI_MIN_MS =
        typeof window.F88_FEED_UI_MIN_MS === 'number' && window.F88_FEED_UI_MIN_MS > 0
            ? window.F88_FEED_UI_MIN_MS
            : 120_000;

    window.latestRealtimePayload = null;
    let lastStatsSignature = null;

    function formatMillions(val) {
        const num = Number(val || 0);
        return `${(num / 1_000_000).toFixed(1)}M`;
    }

    function setText(id, value) {
        const el = document.getElementById(id);
        if (el) el.textContent = value;
    }

    function setHTML(id, value) {
        const el = document.getElementById(id);
        if (el) el.innerHTML = value;
    }

    function setWidth(id, value) {
        const el = document.getElementById(id);
        if (el) el.style.width = `${Math.min(100, Math.max(5, Number(value || 0)))}%`;
    }

    function statsSignature(stats) {
        if (!stats) return '';
        return [
            Number(stats.disbursement || 0),
            Number(stats.collection || 0),
            Number(stats.net_cashflow || 0),
            Number(stats.par1 || 0),
        ].join('|');
    }

    function updateStats(stats) {
        if (!stats) return;
        const sig = statsSignature(stats);
        if (lastStatsSignature !== null && sig === lastStatsSignature) return;
        lastStatsSignature = sig;
        const disb = Number(stats.disbursement || 0);
        const coll = Number(stats.collection || 0);
        const net = Number(stats.net_cashflow || 0);
        const par1 = Number(stats.par1 || 0);

        setText('stat-disbursement', formatMillions(disb));
        setText('stat-collection', formatMillions(coll));
        setText('stat-netcash', formatMillions(net));
        setText('stat-par1', `${par1.toFixed(1)}%`);
        setText('stat-disbursement-trend', '+ realtime');
        setText('stat-collection-trend', '+ realtime');
        setText('stat-par1-trend', `${par1.toFixed(1)}%`);
        setHTML('stat-netcash-trend', net >= 0 ? '<i class="fa-solid fa-arrow-up"></i>Dương' : '<i class="fa-solid fa-triangle-exclamation"></i>Âm');

        setWidth('stat-disbursement-bar', disb / 50_000_000);
        setWidth('stat-collection-bar', coll / 50_000_000);
        setWidth('stat-netcash-bar', Math.abs(net) / 50_000_000);
        setWidth('stat-par1-bar', par1);
    }

    function badgeClass(badge) {
        if (badge === 'danger') return 'badge-danger';
        if (badge === 'success') return 'badge-success';
        return 'badge-warning';
    }

    function feedContentSignature(items) {
        if (!Array.isArray(items)) return '';
        return items
            .map((x) => [x.event_id || '', x.time || '', x.type || '', x.title || '', x.detail || ''].join('\x1e'))
            .join('\x1f');
    }

    function updateFeed(feedItems) {
        if (!Array.isArray(feedItems)) return;
        const sig = feedContentSignature(feedItems);
        if (lastFeedContentSignature !== null && sig === lastFeedContentSignature) return;
        lastFeedContentSignature = sig;
        lastFeedData = feedItems;
        renderFeed();
    }

    function queueFeedUpdate(feedItems) {
        if (!Array.isArray(feedItems)) return;
        pendingFeedItems = feedItems;
        const list = document.getElementById('feedList');
        if (!list) return;
        const now = Date.now();
        if (lastFeedUiAt === 0 || now - lastFeedUiAt >= FEED_UI_MIN_MS) {
            updateFeed(feedItems);
            lastFeedUiAt = now;
        }
    }

    function startFeedUiInterval() {
        if (feedUiIntervalId) return;
        feedUiIntervalId = setInterval(() => {
            const list = document.getElementById('feedList');
            if (!list || !pendingFeedItems) return;
            const now = Date.now();
            if (now - lastFeedUiAt >= FEED_UI_MIN_MS) {
                updateFeed(pendingFeedItems);
                lastFeedUiAt = now;
            }
        }, Math.min(FEED_UI_MIN_MS, 15_000));
    }

    function renderFeed() {
        const feedList = document.getElementById('feedList');
        if (!feedList) return;

        const filtered = lastFeedData.filter(item => currentFeedFilter === 'all' || item.type === currentFeedFilter);
        feedList.innerHTML = '';

        if (filtered.length === 0) {
            feedList.innerHTML = `<li class="feed-item"><div class="feed-content" style="text-align:center;color:rgba(255,255,255,0.35);padding:20px;">Chưa có dữ liệu realtime</div></li>`;
            return;
        }

        filtered.slice(0, 30).forEach(item => {
            const li = document.createElement('li');
            li.className = 'feed-item';
            li.setAttribute('data-type', item.type || 'alert');
            li.innerHTML = `
                <div class="feed-time">${item.time || '--:--'}</div>
                <div class="feed-content">
                    <div class="feed-title">
                        <span class="badge ${badgeClass(item.badge)}">${item.title || 'EVENT'}</span>
                        ${item.detail || ''}
                    </div>
                </div>`;
            feedList.appendChild(li);
        });
        feedList.scrollTop = 0;
    }

    window.filterFeed = function (type, element) {
        currentFeedFilter = type;
        const container = element ? element.closest('.feed-tabs-container') : document;
        container.querySelectorAll('.feed-tab').forEach(tab => tab.classList.remove('active'));
        if (element) element.classList.add('active');
        if (pendingFeedItems && Array.isArray(pendingFeedItems)) {
            lastFeedData = pendingFeedItems;
        }
        renderFeed();
    };

    window.applyRealtimeSnapshot = function (payload) {
        if (!payload || payload.type === 'ping') return;
        window.latestRealtimePayload = payload;
        window.latestRiskRadarMetrics = payload.risk_radar_metrics || null;
        updateStats(payload.stats);
        queueFeedUpdate(payload.feed);
        if (typeof updateRealtimeCharts === 'function') updateRealtimeCharts(payload);
        if (typeof updateVietnamMap === 'function' && Array.isArray(payload.map)) updateVietnamMap(payload.map);
    };

    async function loadInitialSnapshot() {
        try {
            const response = await fetch(`${API_BASE}/api/snapshot`, { cache: 'no-store' });
            if (!response.ok) throw new Error(`snapshot HTTP ${response.status}`);
            const payload = await response.json();
            window.applyRealtimeSnapshot(payload);
            console.log('[F88 realtime] snapshot loaded', payload);
        } catch (err) {
            console.warn('[F88 realtime] failed to load snapshot', err);
        }
    }

    function scheduleReconnect() {
        if (reconnectTimer) return;
        reconnectTimer = setTimeout(() => {
            reconnectTimer = null;
            socketStarted = false;
            startRealtimeSocket();
        }, 2000);
    }

    function startRealtimeSocket() {
        if (socketStarted) return;
        socketStarted = true;
        const wsUrl = `${WS_BASE}/ws/realtime`;
        socket = new WebSocket(wsUrl);
        socket.onopen = () => console.log('[F88 realtime] websocket connected:', wsUrl);
        socket.onmessage = (event) => {
            try { window.applyRealtimeSnapshot(JSON.parse(event.data)); }
            catch (err) { console.warn('[F88 realtime] invalid websocket payload', err); }
        };
        socket.onerror = (err) => console.warn('[F88 realtime] websocket error', err);
        socket.onclose = () => {
            console.warn('[F88 realtime] websocket closed, reconnecting...');
            socketStarted = false;
            scheduleReconnect();
        };
    }

    window.refreshRealtimeSnapshot = async function () {
        try { await fetch(`${API_BASE}/api/recompute`, { method: 'POST' }); } catch (_) {}
        await loadInitialSnapshot();
    };

    window.bootRealtimeDashboard = async function () {
        await loadInitialSnapshot();
        startRealtimeSocket();
        startFeedUiInterval();
    };

    document.addEventListener('DOMContentLoaded', () => window.bootRealtimeDashboard());
})();
