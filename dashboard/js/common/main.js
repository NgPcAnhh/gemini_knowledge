// js/common/main.js

async function switchTab(tabId, element) {
    // Cập nhật UI navigation
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    if (element) {
        element.classList.add('active');
    }

    // Load nội dung HTML
    const container = document.getElementById('main-content-container');
    try {
        const response = await fetch(`html/${tabId}.html`);
        if (!response.ok) throw new Error('Network response was not ok');
        const html = await response.text();
        container.innerHTML = html;
        
        // Khởi tạo các sự kiện giao diện tĩnh (nếu có) sau khi render HTML
        initDraggableFAB();

        // Tùy theo tab mà khởi tạo biểu đồ tương ứng
        if (tabId === 'tab-realtime') {
            if (typeof initVietnamMap === 'function') initVietnamMap();
            if (typeof initRealtimeCharts === 'function') initRealtimeCharts();
        } else if (tabId === 'tab-revenue') {
            if (typeof initRevenueCharts === 'function') initRevenueCharts();
        } else if (tabId === 'tab-risk') {
            if (typeof initRiskCharts === 'function') initRiskCharts();
        } else if (tabId === 'tab-customer') {
            if (typeof initCustomerCharts === 'function') initCustomerCharts();
        }

    } catch (error) {
        console.error('Lỗi khi tải tab:', error);
        container.innerHTML = `<div style="padding: 20px; color: var(--danger);">Lỗi khi tải nội dung tab. Chắc chắn bạn đang chạy ứng dụng qua Local Server (http://) chứ không phải file://</div>`;
    }
}

// Floating Filter Toggle
function toggleCardFilter(panelId) {
    const panel = document.getElementById(panelId);
    if (!panel) return;
    const overlay = panel.closest('.filter-overlay');
    if (overlay) {
        overlay.classList.toggle('active');
    }
}

// Draggable FAB Logic
function initDraggableFAB() {
    const buttons = document.querySelectorAll('.floating-filter-btn');
    buttons.forEach(btn => {
        // Tránh gắn lại event nhiều lần nếu đã gắn
        if (btn.hasAttribute('data-fab-init')) return;
        btn.setAttribute('data-fab-init', 'true');

        let isDragging = false;
        let startX, startY, initialX, initialY;
        let dragThreshold = 5; // pixels to distinguish click from drag

        btn.addEventListener('mousedown', (e) => {
            isDragging = false;
            startX = e.clientX;
            startY = e.clientY;
            
            const rect = btn.getBoundingClientRect();
            initialX = rect.left;
            initialY = rect.top;

            const onMouseMove = (e) => {
                const dx = e.clientX - startX;
                const dy = e.clientY - startY;
                
                if (Math.abs(dx) > dragThreshold || Math.abs(dy) > dragThreshold) {
                    isDragging = true;
                    // Switch to top/left for positioning
                    btn.style.bottom = 'auto';
                    btn.style.right = 'auto';
                    btn.style.left = (initialX + dx) + 'px';
                    btn.style.top = (initialY + dy) + 'px';
                }
            };

            const onMouseUp = () => {
                document.removeEventListener('mousemove', onMouseMove);
                document.removeEventListener('mouseup', onMouseUp);
                
                if (!isDragging) {
                    // Only toggle filter if we didn't drag
                    const panelId = btn.getAttribute('data-panel');
                    toggleCardFilter(panelId);
                }
            };

            document.addEventListener('mousemove', onMouseMove);
            document.addEventListener('mouseup', onMouseUp);
        });
    });
}

// Sidebar toggle
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
    // Invalidate Leaflet map size after transition
    setTimeout(() => { if (window._vnMap) window._vnMap.invalidateSize(); }, 350);
}

function refreshData(btn) {
    btn.classList.add('spin');
    setTimeout(() => btn.classList.remove('spin'), 800);
}

// Feed filtering
function filterFeed(type, element) {
    document.querySelectorAll('.feed-tab').forEach(el => el.classList.remove('active'));
    element.classList.add('active');
    document.querySelectorAll('.feed-item').forEach(item => {
        if(type === 'all' || item.getAttribute('data-type') === type) {
            item.classList.remove('hidden');
        } else {
            item.classList.add('hidden');
        }
    });
}

window.onload = function() {
    // Tải tab mặc định khi trang web vừa tải xong
    const defaultActiveNav = document.querySelector('.nav-item.active');
    switchTab('tab-realtime', defaultActiveNav);
};
