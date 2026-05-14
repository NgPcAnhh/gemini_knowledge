// js/common/main.js

async function switchTab(tabId, element) {
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    if (element) element.classList.add('active');

    const container = document.getElementById('main-content-container');
    try {
        const response = await fetch(`html/${tabId}.html`, { cache: 'no-store' });
        if (!response.ok) throw new Error(`Cannot fetch html/${tabId}.html`);
        const html = await response.text();
        container.innerHTML = html;

        initDraggableFAB();

        if (tabId === 'tab-realtime') {
            if (typeof initVietnamMap === 'function') initVietnamMap();
            if (typeof initRealtimeCharts === 'function') initRealtimeCharts();

            if (typeof window.bootRealtimeDashboard === 'function') {
                window.bootRealtimeDashboard();
            }
            if (window.latestRealtimePayload && typeof window.applyRealtimeSnapshot === 'function') {
                window.applyRealtimeSnapshot(window.latestRealtimePayload);
            }
        } else if (tabId === 'tab-revenue') {
            if (typeof initRevenueCharts === 'function') initRevenueCharts();
        } else if (tabId === 'tab-risk') {
            if (typeof initRiskCharts === 'function') initRiskCharts();
        } else if (tabId === 'tab-customer') {
            if (typeof initCustomerCharts === 'function') initCustomerCharts();
        }

        setTimeout(() => {
            if (window._vnMap && typeof window._vnMap.invalidateSize === 'function') {
                window._vnMap.invalidateSize();
            }
        }, 300);
    } catch (error) {
        console.error('Lỗi khi tải tab:', error);
        container.innerHTML = `<div style="padding:20px;color:var(--danger);">Lỗi khi tải nội dung tab. Hãy chạy dashboard qua local server/http, không mở bằng file://</div>`;
    }
}

function toggleCardFilter(panelId) {
    const panel = document.getElementById(panelId);
    if (!panel) return;
    const overlay = panel.closest('.filter-overlay');
    if (overlay) overlay.classList.toggle('active');
}

function initDraggableFAB() {
    const buttons = document.querySelectorAll('.floating-filter-btn');
    buttons.forEach(btn => {
        if (btn.hasAttribute('data-fab-init')) return;
        btn.setAttribute('data-fab-init', 'true');

        let isDragging = false;
        let startX, startY, initialX, initialY;
        const dragThreshold = 5;

        btn.addEventListener('mousedown', (e) => {
            isDragging = false;
            startX = e.clientX;
            startY = e.clientY;

            const rect = btn.getBoundingClientRect();
            initialX = rect.left;
            initialY = rect.top;

            const onMouseMove = (moveEvt) => {
                const dx = moveEvt.clientX - startX;
                const dy = moveEvt.clientY - startY;

                if (Math.abs(dx) > dragThreshold || Math.abs(dy) > dragThreshold) {
                    isDragging = true;
                    btn.style.bottom = 'auto';
                    btn.style.right = 'auto';
                    btn.style.left = `${initialX + dx}px`;
                    btn.style.top = `${initialY + dy}px`;
                }
            };

            const onMouseUp = () => {
                document.removeEventListener('mousemove', onMouseMove);
                document.removeEventListener('mouseup', onMouseUp);

                if (!isDragging) {
                    const panelId = btn.getAttribute('data-panel');
                    toggleCardFilter(panelId);
                }
            };

            document.addEventListener('mousemove', onMouseMove);
            document.addEventListener('mouseup', onMouseUp);
        });
    });
}

function toggleSidebar() {
    const sidebar = document.getElementById('sidebar');
    const icon = document.getElementById('toggleIcon');
    sidebar.classList.toggle('collapsed');

    if (sidebar.classList.contains('collapsed')) {
        icon.classList.remove('fa-angles-left');
        icon.classList.add('fa-angles-right');
    } else {
        icon.classList.remove('fa-angles-right');
        icon.classList.add('fa-angles-left');
    }

    setTimeout(() => {
        if (window._vnMap) window._vnMap.invalidateSize();
    }, 350);
}

function refreshData(btn) {
    if (btn) btn.classList.add('spin');
    if (typeof window.refreshRealtimeSnapshot === 'function') {
        window.refreshRealtimeSnapshot();
    }
    setTimeout(() => {
        if (btn) btn.classList.remove('spin');
    }, 800);
}

function filterFeed(type, element) {
    document.querySelectorAll('.feed-tab').forEach(el => el.classList.remove('active'));
    if (element) element.classList.add('active');
    document.querySelectorAll('.feed-item').forEach(item => {
        if (type === 'all' || item.getAttribute('data-type') === type) item.classList.remove('hidden');
        else item.classList.add('hidden');
    });
}

window.onload = function () {
    const defaultActiveNav = document.querySelector('.nav-item.active');
    switchTab('tab-realtime', defaultActiveNav);
};
