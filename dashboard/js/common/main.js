// js/common/main.js

async function switchTab(tabId, element) {
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    if (element) element.classList.add('active');

    // Clear active polling intervals to prevent memory leaks and overlapping requests
    if (window.tabIntervalId) {
        clearInterval(window.tabIntervalId);
        window.tabIntervalId = null;
    }

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
            if (typeof initRevenueCharts === 'function') {
                initRevenueCharts();
                // Set up 1-minute auto-refresh
                window.tabIntervalId = setInterval(initRevenueCharts, 60000);
            }
        } else if (tabId === 'tab-risk') {
            if (typeof initRiskCharts === 'function') {
                initRiskCharts();
                // Set up 1-minute auto-refresh
                window.tabIntervalId = setInterval(initRiskCharts, 60000);
            }
        } else if (tabId === 'tab-customer') {
            if (typeof initCustomerCharts === 'function') {
                initCustomerCharts();
                // Set up 1-minute auto-refresh
                window.tabIntervalId = setInterval(initCustomerCharts, 60000);
            }
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
    // Instantly refresh other analytical charts if they are currently rendered on the page
    if (typeof window.initRevenueCharts === 'function' && document.getElementById('ticketSizeDistribution')) {
        window.initRevenueCharts();
    }
    if (typeof window.initRiskCharts === 'function' && document.getElementById('riskBubbleChart')) {
        window.initRiskCharts();
    }
    if (typeof window.initCustomerCharts === 'function' && document.getElementById('ageIncomeBubblePAR')) {
        window.initCustomerCharts();
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

// Event List Modal Logic
window.openEventListModal = function(type, filterValue = null) {
    const modal = document.getElementById('eventListModal');
    const tableBody = document.getElementById('eventTableBody');
    const titleEl = document.getElementById('modalTitle');
    const loadingEl = document.getElementById('modalLoading');
    const noDataEl = document.getElementById('modalNoData');
    const tableEl = document.getElementById('eventTable');

    if (!modal || !tableBody) return;

    modal.classList.add('active');
    tableBody.innerHTML = '';
    loadingEl.style.display = 'block';
    noDataEl.style.display = 'none';
    tableEl.style.display = 'none';

    // Xác định tiêu đề và filter
    let title = 'Danh sách sự kiện';
    let filterFn = () => true;

    const payload = window.latestRealtimePayload;
    const feed = (payload && payload.feed) ? payload.feed : [];

    if (type === 'disbursed') {
        title = 'Danh sách Giải ngân (Real-time)';
        filterFn = (item) => item.title && item.title.includes('GIẢI NGÂN');
    } else if (type === 'repayment') {
        title = 'Danh sách Thu nợ (Real-time)';
        filterFn = (item) => item.title && item.title.includes('THU NỢ');
    } else if (type === 'approved') {
        title = 'Danh sách Phê duyệt (Real-time)';
        filterFn = (item) => item.title && item.title.includes('PHÊ DUYỆT');
    } else if (type === 'rejected') {
        title = 'Danh sách Từ chối (Real-time)';
        filterFn = (item) => item.title && item.title.includes('TỪ CHỐI');
    } else if (type === 'overdue' || type === 'late') {
        title = 'Danh sách Nợ xấu / Trả chậm';
        filterFn = (item) => {
            if (!item.title) return false;
            const t = item.title.toUpperCase();
            const d = (item.detail || "").toUpperCase();
            return t.includes('TRỄ') || t.includes('QUÁ HẠN') || t.includes('NỢ XẤU') || 
                   (t.includes('TRẠNG THÁI') && (d.includes('QUÁ HẠN') || d.includes('NỢ XẤU')));
        };
    } else if (type === 'product') {
        title = `Danh sách hồ sơ: ${filterValue}`;
        filterFn = (item) => {
            if (!item.loan_type) return false;
            const lt = item.loan_type.toLowerCase();
            if (filterValue === 'Xe máy') return lt.includes('xe máy');
            if (filterValue === 'Ô tô') return lt.includes('ô tô');
            if (filterValue === 'Điện thoại/Laptop') return lt.includes('điện thoại') || lt.includes('laptop');
            if (filterValue === 'Bất động sản') return lt.includes('bất động sản') || lt.includes('sổ đỏ');
            if (filterValue === 'Khác') return !lt.includes('xe máy') && !lt.includes('ô tô') && !lt.includes('điện thoại') && !lt.includes('laptop') && !lt.includes('bất động sản') && !lt.includes('sổ đỏ');
            return false;
        };
    }

    titleEl.textContent = title;

    // Giả lập delay một chút cho mượt
    setTimeout(() => {
        const filtered = feed.filter(filterFn);
        loadingEl.style.display = 'none';

        if (filtered.length === 0) {
            noDataEl.style.display = 'block';
        } else {
            tableEl.style.display = 'table';
            filtered.forEach(item => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td style="white-space:nowrap;color:var(--text-muted)">${item.time || '--:--'}</td>
                    <td><span class="badge ${item.badge === 'success' ? 'badge-success' : (item.badge === 'danger' ? 'badge-danger' : 'badge-warning')}">${item.title}</span></td>
                    <td style="width:100%">${item.detail}</td>
                `;
                tableBody.appendChild(tr);
            });
        }
    }, 300);
};

window.closeEventListModal = function() {
    const modal = document.getElementById('eventListModal');
    if (modal) modal.classList.remove('active');
};
