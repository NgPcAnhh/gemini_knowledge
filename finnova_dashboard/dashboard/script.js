document.addEventListener('DOMContentLoaded', () => {
    // State trackers to prevent re-initialization
    let isHieuQuaInit = false;
    let isRuiRoInit = false;
    let isChanDungInit = false;

    // 1. Tab switching logic
    const navItems = document.querySelectorAll('.nav-item');
    const tabPanes = document.querySelectorAll('.tab-pane');
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            // Remove active from all nav items
            navItems.forEach(nav => nav.classList.remove('active'));
            // Add active to clicked item
            item.classList.add('active');
            // Hide all tabs
            tabPanes.forEach(tab => tab.classList.remove('active'));

            // Show targeted tab
            const targetId = item.getAttribute('data-tab');
            if (targetId) {
                const targetPane = document.getElementById(targetId);
                targetPane.classList.add('active');
                
                // Small timeout to ensure browser has rendered the 'active' state (display: flex)
                // before Chart.js tries to calculate dimensions.
                setTimeout(() => {
                    if (targetId === 'tab-hieuqua' && !isHieuQuaInit) {
                        initHieuQuaTab();
                        isHieuQuaInit = true;
                    }
                    if (targetId === 'tab-ruiro' && !isRuiRoInit) {
                        initRuiRoTab();
                        isRuiRoInit = true;
                    }
                    if (targetId === 'tab-chandung' && !isChanDungInit) {
                        initChanDungTab();
                        isChanDungInit = true;
                    }
                }, 50);
            }
        });
    });
    // 2. Real-time Clock
    function updateClock() {
        const now = new Date();

        // Format time
        const timeStr = now.toLocaleTimeString('vi-VN', {
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit',
            hour12: false
        });
        document.getElementById('current-time').textContent = timeStr;
        // Format date
        const dateStr = now.toLocaleDateString('vi-VN', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        });
        document.getElementById('current-date').textContent = dateStr;
    }
    setInterval(updateClock, 1000);
    updateClock(); // initial call

    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebarToggle');
    if (sidebar && sidebarToggle) {
        sidebarToggle.addEventListener('click', () => {
            sidebar.classList.toggle('sidebar-collapsed');
            if (sidebar.classList.contains('sidebar-collapsed')) {
                sidebarToggle.textContent = '›';
                sidebarToggle.setAttribute('aria-label', 'Mở rộng sidebar');
            } else {
                sidebarToggle.textContent = '‹';
                sidebarToggle.setAttribute('aria-label', 'Thu gọn sidebar');
            }
        });
    }

    // Global resize listener for Leaflet maps
    window.addEventListener('resize', () => {
        const maps = document.querySelectorAll('.leaflet-container');
        maps.forEach(m => {
            if (m._leaflet_map) {
                m._leaflet_map.invalidateSize();
            }
        });
    });

    // Register ChartDataLabels plugin for Chart.js
    if (typeof ChartDataLabels !== 'undefined') {
        Chart.register(ChartDataLabels);
    }
    // Initialize ONLY the first active tab (Real-time)
    initRealTimeTab();
});
async function initRealTimeTab() {
    // 1. Vietnam Map with Leaflet
    const mapContainerId = 'vietnam-map';
    const mapContainer = document.getElementById(mapContainerId);
    if (mapContainer && typeof L !== 'undefined') {
        const vnBounds = L.latLngBounds([8.5, 102.0], [23.5, 109.5]);
        const map = L.map(mapContainerId, {
            renderer: L.canvas({ padding: 0.5 }),
            zoomControl: true,
            attributionControl: false,
            minZoom: 5,
            maxZoom: 13
        });
        map.fitBounds(vnBounds);
        L.tileLayer('https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png', { maxZoom: 19 }).addTo(map);

        // Fetch GeoJSON for provinces (Optional, markers should show even if this fails)
        fetch('https://raw.githubusercontent.com/TungTh/tungth.github.io/master/data/vietnam.geojson')
            .then(r => r.json())
            .then(data => {
                L.geoJSON(data, {
                    style: { color: '#00a651', weight: 1, opacity: 0.3, fillColor: '#00a651', fillOpacity: 0.02 }
                }).addTo(map);
            }).catch(e => console.warn('GeoJSON load failed:', e));

        // Initialize 500 branches strictly on land with high density in Thanh-Nghe-Tinh
        const branches = [];
        const provinces = [
            { name: 'Thanh Hóa', lat: 19.8067, lng: 105.7000, count: 65 }, // High density
            { name: 'Nghệ An', lat: 18.6734, lng: 105.6000, count: 75 },   // High density
            { name: 'Hà Tĩnh', lat: 18.3427, lng: 105.8000, count: 50 },   // Added & High density
            { name: 'Hà Nội', lat: 21.0285, lng: 105.8542, count: 45 },
            { name: 'TP.HCM', lat: 10.8231, lng: 106.6297, count: 55 },
            { name: 'Đà Nẵng', lat: 16.0544, lng: 108.1500, count: 20 },
            { name: 'Hải Phòng', lat: 20.8449, lng: 106.6000, count: 15 },
            { name: 'Cần Thơ', lat: 10.0452, lng: 105.7469, count: 15 },
            { name: 'Đồng Nai', lat: 10.9574, lng: 106.8427, count: 12 },
            { name: 'Bình Dương', lat: 10.9804, lng: 106.6519, count: 12 },
            { name: 'Quảng Ninh', lat: 21.0500, lng: 107.1000, count: 10 },
            { name: 'Khánh Hòa', lat: 12.2467, lng: 109.0500, count: 10 },
            { name: 'Lâm Đồng', lat: 11.9404, lng: 108.4583, count: 10 },
            { name: 'Gia Lai', lat: 13.9822, lng: 108.0059, count: 10 },
            { name: 'Đắk Lắk', lat: 12.6667, lng: 108.0500, count: 10 },
            { name: 'Bình Định', lat: 13.7820, lng: 109.1000, count: 8 },
            { name: 'Quảng Nam', lat: 15.5670, lng: 108.3000, count: 8 },
            { name: 'Lạng Sơn', lat: 21.8548, lng: 106.7620, count: 8 },
            { name: 'Lào Cai', lat: 22.4856, lng: 103.9707, count: 8 },
            { name: 'Sơn La', lat: 21.3236, lng: 103.9213, count: 8 },
            { name: 'Cà Mau', lat: 9.1769, lng: 105.0500, count: 8 },
            { name: 'Kiên Giang', lat: 10.0125, lng: 105.0000, count: 8 },
            { name: 'An Giang', lat: 10.5000, lng: 105.1000, count: 8 },
            { name: 'Thái Nguyên', lat: 21.5939, lng: 105.8442, count: 8 },
            { name: 'Vĩnh Phúc', lat: 21.3114, lng: 105.5471, count: 8 },
            { name: 'Tây Ninh', lat: 11.3323, lng: 106.1265, count: 8 },
            { name: 'Bình Thuận', lat: 10.9333, lng: 108.0500, count: 8 },
            { name: 'Hưng Yên', lat: 20.6464, lng: 106.0511, count: 8 },
            { name: 'Bắc Giang', lat: 21.2731, lng: 106.1946, count: 8 }
        ];

        const getMarkerColor = (badDebt) => {
            if (badDebt >= 4.0) return '#ef4444'; // Red (Bad)
            if (badDebt >= 2.0) return '#f97316'; // Orange
            if (badDebt >= 1.0) return '#fcd34d'; // Yellow (Warning)
            if (badDebt >= 0.5) return '#10b981'; // Green
            return '#059669'; // Deep Green (Good)
        };

        const createTooltipHTML = (b) => `
            <div style="font-family: 'Inter', sans-serif; padding: 5px; min-width: 160px;">
                <div style="font-weight: 800; color: #005a32; margin-bottom: 5px; border-bottom: 1px solid #eee; padding-bottom: 3px;">
                    F88 #${b.id} - ${b.province}
                </div>
                <div style="font-size: 11px; color: #444; line-height: 1.6;">
                    <div style="display:flex; justify-content:space-between"><span>Hợp đồng:</span> <b>${b.contracts}</b></div>
                    <div style="display:flex; justify-content:space-between"><span>Giải ngân:</span> <b>${b.disbursed.toLocaleString()} tr</b></div>
                    <div style="display:flex; justify-content:space-between"><span>Dư nợ:</span> <b>${b.debt.toLocaleString()} tr</b></div>
                    <div style="display:flex; justify-content:space-between; margin-top:3px; padding-top:3px; border-top:1px dashed #ddd;">
                        <span>Tỷ lệ nợ xấu:</span> <b style="color:${b.badDebt > 2 ? '#ef4444' : '#059669'}">${b.badDebt.toFixed(1)}%</b>
                    </div>
                </div>
            </div>`;

        // Calculate total count and adjust last province to reach exactly 500 if needed
        const totalSet = provinces.reduce((s, p) => s + p.count, 0);
        if (totalSet < 500) provinces[0].count += (500 - totalSet);

        provinces.forEach(p => {
            for (let i = 0; i < p.count; i++) {
                // Tight jitter (0.25) to prevent sea markers while keeping dispersion
                const lat = p.lat + (Math.random() - 0.5) * 0.25;
                const lng = p.lng + (Math.random() - 0.5) * 0.25;
                
                const badDebt = Math.random() * 5.0; 
                const branch = {
                    id: branches.length + 100,
                    province: p.name,
                    contracts: Math.floor(Math.random() * 150) + 20,
                    disbursed: Math.floor(Math.random() * 800) + 100,
                    debt: Math.floor(Math.random() * 3000) + 500,
                    badDebt: badDebt
                };

                const marker = L.circleMarker([lat, lng], {
                    radius: 2.5,
                    fillColor: getMarkerColor(badDebt),
                    color: '#fff',
                    weight: 0.5,
                    opacity: 1,
                    fillOpacity: 0.85
                }).addTo(map);

                marker.bindTooltip(() => createTooltipHTML(branch), { sticky: true });
                branch.marker = marker;
                branches.push(branch);
            }
        });

        // Simulation loop every 5 seconds
        setInterval(() => {
            branches.forEach(b => {
                if (Math.random() > 0.88) { // 12% activity
                    b.contracts += Math.floor(Math.random() * 2);
                    b.disbursed += Math.floor(Math.random() * 20);
                    b.debt += Math.floor(Math.random() * 15);
                    b.badDebt = Math.max(0, Math.min(6, b.badDebt + (Math.random() - 0.5) * 0.2));
                    
                    const color = getMarkerColor(b.badDebt);
                    b.marker.setStyle({ fillColor: color });

                    const originalRadius = b.marker.options.radius;
                    b.marker.setRadius(originalRadius + 1.5);
                    setTimeout(() => b.marker.setRadius(originalRadius), 1000);
                }
            });
        }, 5000);

        map.invalidateSize();
    }

    // Colors
    const colorPrimary = '#005a32';
    const colorOrange = '#f97316';
    const colorRed = '#ef4444';
    const colorGreen = '#10b981';

    // Standardized Donut Options
    const donutOptions = {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '55%', // Thicker rings
        plugins: {
            legend: {
                position: 'right', // Legend on the right
                labels: {
                    boxWidth: 8,
                    usePointStyle: true,
                    padding: 8,
                    font: { size: 9 }
                }
            },
            datalabels: { display: false }
        }
    };

    // 2. Doughnut 1: Loại hình
    if (document.getElementById('chart-loaihinh')) {
        new Chart(document.getElementById('chart-loaihinh'), {
            type: 'doughnut',
            data: {
                labels: ['Tín chấp', 'Thế chấp'],
                datasets: [{
                    data: [1764, 694],
                    backgroundColor: [colorOrange, colorPrimary],
                    borderWidth: 0
                }]
            },
            options: donutOptions
        });
    }
    // 3. Doughnut 2: Tình trạng
    if (document.getElementById('chart-tinhtrang')) {
        new Chart(document.getElementById('chart-tinhtrang'), {
            type: 'doughnut',
            data: {
                labels: ['Trước hạn', 'Đúng hạn', 'B1 (0-30 ngày)', 'B2 (30-60 ngày)', 'B3 (60-90 ngày)', 'B4 (>90 ngày)'],
                datasets: [{
                    data: [1506, 535, 180, 103, 75, 56],
                    backgroundColor: [colorPrimary, colorGreen, '#fcd34d', '#f97316', '#ef4444', '#b91c1c'],
                    borderWidth: 0
                }]
            },
            options: donutOptions
        });
    }
    // 4. Doughnut 3: Khách hàng sử dụng dịch vụ
    if (document.getElementById('chart-dichvu')) {
        new Chart(document.getElementById('chart-dichvu'), {
            type: 'doughnut',
            data: {
                labels: ['Chi nhánh', 'App'],
                datasets: [{
                    data: [1672, 786],
                    backgroundColor: [colorPrimary, colorOrange],
                    borderWidth: 0
                }]
            },
            options: donutOptions
        });
    }
    // 5. Bar Chart: Phân bổ mức khoản vay (Histogram Style)
    if (document.getElementById('chart-mucvay')) {
        new Chart(document.getElementById('chart-mucvay'), {
            type: 'bar',
            data: {
                labels: ['3-10tr', '10-20tr', '20-50tr', '50-100tr', '100-200tr', '200-500tr', '500-1tỷ', '1-2tỷ', '>2tỷ'],
                datasets: [
                    {
                        label: 'Số hợp đồng',
                        data: [1245, 852, 1029, 617, 428, 215, 96, 42, 18],
                        backgroundColor: colorPrimary,
                        barPercentage: 0.9, 
                        categoryPercentage: 0.9,
                        borderRadius: 2,
                        order: 2
                    },
                    {
                        label: 'Cùng kỳ năm trước',
                        data: [1100, 950, 800, 750, 350, 300, 150, 80, 50], // Independent wavy data
                        type: 'line',
                        borderColor: colorOrange,
                        borderWidth: 2,
                        fill: false,
                        tension: 0.4, 
                        pointRadius: 0, 
                        order: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: {
                    mode: 'index',
                    intersect: false,
                },
                plugins: {
                    legend: { display: false },
                    datalabels: {
                        display: (ctx) => ctx.datasetIndex === 0, // Only show for bars
                        align: 'top',
                        anchor: 'end',
                        color: '#000',
                        font: { weight: 'bold', size: 8 }
                    }
                },
                scales: {
                    y: { beginAtZero: true, display: false },
                    x: { grid: { display: false }, ticks: { font: { size: 8 } } }
                }
            }
        });
    }
    // 6. Real-time Revenue & Profit Chart (ECharts)
    const chartDom = document.getElementById('chart-doanhthu');
    if (chartDom) {
        const myChart = echarts.init(chartDom);
        let revenueData = [];
        let now = new Date();
        let startOfDay = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 0, 0, 0);
        
        const timeStep = 30 * 1000; // 30-second history intervals
        let currentLoopTime = startOfDay.getTime();
        
        let lastRev = 20 + Math.random() * 10;

        // Generate past data from start of day to now
        while (currentLoopTime <= now.getTime()) {
            lastRev = Math.max(0, lastRev + (Math.random() - 0.48) * 4);
            revenueData.push([currentLoopTime, parseFloat(lastRev.toFixed(2))]);
            currentLoopTime += timeStep;
        }

        const option = {
            color: ['#005a32'],
            tooltip: {
                trigger: 'axis',
                backgroundColor: 'rgba(255, 255, 255, 0.95)',
                borderWidth: 0,
                shadowBlur: 10,
                shadowColor: 'rgba(0,0,0,0.1)',
                textStyle: { color: '#333', fontSize: 12 },
                formatter: function (params) {
                    let date = new Date(params[0].value[0]);
                    let timeStr = date.toLocaleTimeString('vi-VN', { hour12: false });
                    let res = `<div style="font-weight:600;margin-bottom:4px;">${timeStr}</div>`;
                    params.forEach(item => {
                        res += `<div style="display:flex;justify-content:space-between;gap:20px;">
                            <span>${item.marker} ${item.seriesName}</span>
                            <span style="font-weight:600">${item.value[1]} triệu</span>
                        </div>`;
                    });
                    return res;
                }
            },
            legend: {
                data: ['Doanh thu'],
                right: 10,
                top: 0,
                icon: 'circle',
                itemWidth: 8,
                textStyle: { fontSize: 11, color: '#666' }
            },
            grid: {
                left: '20',
                right: '20',
                bottom: '10',
                top: '40',
                containLabel: true
            },
            xAxis: {
                type: 'time',
                boundaryGap: false,
                axisLine: { lineStyle: { color: '#eee' } },
                axisLabel: { color: '#999', fontSize: 10 },
                splitLine: { show: false }
            },
            yAxis: {
                type: 'value',
                axisLabel: { color: '#999', fontSize: 10, formatter: '{value} tr' },
                splitLine: { lineStyle: { type: 'dashed', color: '#f0f0f0' } }
            },
            dataZoom: [
                {
                    type: 'inside',
                    xAxisIndex: 0,
                    filterMode: 'none'
                }
            ],
            series: [
                {
                    name: 'Doanh thu',
                    type: 'line',
                    smooth: true,
                    showSymbol: false,
                    data: revenueData,
                    lineStyle: { width: 3 },
                    areaStyle: {
                        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                            { offset: 0, color: 'rgba(0, 90, 50, 0.2)' },
                            { offset: 1, color: 'rgba(0, 90, 50, 0)' }
                        ])
                    }
                }
            ]
        };

        myChart.setOption(option);

        setInterval(function () {
            let now = new Date();
            lastRev = Math.max(0, lastRev + (Math.random() - 0.48) * 8);
            revenueData.push([now.getTime(), parseFloat(lastRev.toFixed(2))]);

            myChart.setOption({
                series: [
                    { data: revenueData }
                ]
            });
        }, 10000);

        window.addEventListener('resize', () => myChart.resize());
    }
}
function initHieuQuaTab() {
    const colorPrimary = '#005a32';
    const colorOrange = '#f97316';
    const colorYellow = '#f59e0b';
    const colorGray = '#9ca3af';
    // 1. Phân bổ nguồn chi phí
    if (document.getElementById('hq-chart-chiphi')) {
        new Chart(document.getElementById('hq-chart-chiphi'), {
            type: 'doughnut',
            data: {
                labels: ['Marketing', 'Vận hành', 'Nhân sự', 'Đối tác', 'Khác'],
                datasets: [{
                    data: [7.05, 4.18, 3.36, 2.41, 0.83],
                    backgroundColor: [colorOrange, colorPrimary, colorYellow, '#34d399', colorGray],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '60%',
                plugins: {
                    legend: { position: 'right', labels: { boxWidth: 10, usePointStyle: true, font: { size: 10 } } },
                    datalabels: { display: false }
                }
            }
        });
    }
    // 2. Doanh thu & lợi nhuận theo tháng
    if (document.getElementById('hq-chart-dtlnthang')) {
        new Chart(document.getElementById('hq-chart-dtlnthang'), {
            type: 'line',
            data: {
                labels: Array.from({ length: 12 }, (_, i) => `T${i + 1}`),
                datasets: [
                    {
                        label: 'Doanh thu',
                        data: [2.4, 2.7, 3.1, 3.3, 3.7, 3.9, 3.4, 3.8, 4.0, 4.2, 4.6, 4.7],
                        borderColor: colorPrimary,
                        backgroundColor: colorPrimary,
                        tension: 0.3
                    },
                    {
                        label: 'Lợi nhuận',
                        data: [0.5, 0.6, 0.7, 0.8, 0.9, 1.1, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4],
                        borderColor: colorOrange,
                        backgroundColor: colorOrange,
                        tension: 0.3
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'top', labels: { boxWidth: 10, usePointStyle: true } }, datalabels: { display: false } },
                scales: { x: { grid: { display: false } }, y: { display: false } }
            }
        });
    }
    // 3. Phân bổ các mức khoản vay
    if (document.getElementById('hq-chart-mucvay')) {
        new Chart(document.getElementById('hq-chart-mucvay'), {
            type: 'bar',
            data: {
                labels: ['< 20 triệu', '20 - 50 triệu', '50 - 100 triệu', '100 - 150 triệu', '150 - 200 triệu', '> 200 triệu'],
                datasets: [{
                    data: [0.34, 0.88, 1.49, 2.21, 1.67, 1.49],
                    backgroundColor: colorPrimary,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false }, datalabels: { display: true, align: 'top', anchor: 'end' } },
                scales: { x: { grid: { display: false }, ticks: { font: { size: 9 } } }, y: { display: false } }
            }
        });
    }
    // 4. Doanh thu trên mỗi hợp đồng theo tháng
    if (document.getElementById('hq-chart-dthdthang')) {
        new Chart(document.getElementById('hq-chart-dthdthang'), {
            type: 'line',
            data: {
                labels: Array.from({ length: 12 }, (_, i) => `T${i + 1}`),
                datasets: [{
                    label: 'Triệu VND',
                    data: [13.6, 14.1, 14.4, 14.9, 15.2, 15.5, 16.1, 16.8, 17.2, 17.6, 17.9, 18.4],
                    borderColor: colorPrimary,
                    backgroundColor: colorPrimary,
                    tension: 0.3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false }, datalabels: { display: true, align: 'top', font: { size: 9 } } },
                scales: { x: { grid: { display: false } }, y: { display: false, min: 10, max: 25 } }
            }
        });
    }
    // 5. Tăng trưởng số hợp đồng và doanh thu
    if (document.getElementById('hq-chart-tangtruong')) {
        new Chart(document.getElementById('hq-chart-tangtruong'), {
            type: 'bar',
            data: {
                labels: Array.from({ length: 12 }, (_, i) => `T${i + 1}`),
                datasets: [
                    {
                        type: 'line',
                        label: 'Tăng trưởng doanh thu (%)',
                        data: [12, 15, 14, 18, 16, 20, 15, 19, 22, 18, 24, 25],
                        borderColor: colorOrange,
                        backgroundColor: colorOrange,
                        yAxisID: 'y1'
                    },
                    {
                        type: 'bar',
                        label: 'Số hợp đồng',
                        data: [500, 650, 700, 850, 800, 950, 1100, 1300, 1400, 1491, 1475, 1720],
                        backgroundColor: colorPrimary,
                        yAxisID: 'y'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'top', labels: { boxWidth: 10, usePointStyle: true, font: { size: 10 } } }, datalabels: { display: false } },
                scales: {
                    x: { grid: { display: false } },
                    y: { display: false, position: 'left' },
                    y1: { display: false, position: 'right', min: 0, max: 50 }
                }
            }
        });
    }
    // 6. Cấu trúc chi phí
    if (document.getElementById('hq-chart-cautruc-cp')) {
        new Chart(document.getElementById('hq-chart-cautruc-cp'), {
            type: 'bar',
            data: {
                labels: Array.from({ length: 12 }, (_, i) => `T${i + 1}`),
                datasets: [
                    {
                        label: 'Chi phí biến đổi',
                        data: [4.3, 4.5, 4.7, 4.8, 5.0, 5.1, 5.4, 5.6, 5.8, 6.1, 6.2, 6.5],
                        backgroundColor: colorPrimary
                    },
                    {
                        label: 'Chi phí cố định',
                        data: [6.1, 6.3, 6.7, 6.9, 7.0, 7.4, 7.7, 7.9, 8.3, 10.1, 10.4, 10.6],
                        backgroundColor: colorOrange
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { stacked: true, grid: { display: false } },
                    y: { stacked: true, display: false }
                },
                plugins: { legend: { position: 'top', labels: { boxWidth: 10, usePointStyle: true, font: { size: 10 } } }, datalabels: { display: true, color: '#fff', font: { size: 9 } } }
            }
        });
    }
    // 7. Cấu trúc EBIT
    if (document.getElementById('hq-chart-ebit')) {
        // Waterfall logic via bar chart tricks
        new Chart(document.getElementById('hq-chart-ebit'), {
            type: 'bar',
            data: {
                labels: ['Doanh thu', 'Chi phí trực tiếp', 'Chi phí Marketing', 'Chi phí Vận hành', 'Chi phí Khác', 'EBIT'],
                datasets: [
                    {
                        label: 'Invisible base',
                        data: [0, 23.53, 16.48, 13.12, 12.55, 0],
                        backgroundColor: 'transparent',
                        borderColor: 'transparent'
                    },
                    {
                        label: 'Waterfall',
                        data: [34.68, -11.15, -7.05, -3.36, -0.57, 12.55],
                        backgroundColor: (ctx) => {
                            const val = ctx.raw;
                            if (ctx.dataIndex === 0 || ctx.dataIndex === 5) return colorPrimary;
                            return val < 0 ? colorOrange : colorPrimary;
                        },
                        borderRadius: 4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: { x: { stacked: true, grid: { display: false }, ticks: { font: { size: 9 } } }, y: { stacked: true, display: false } },
                plugins: { legend: { display: false }, datalabels: { display: true, anchor: 'end', align: 'top', formatter: (val) => val !== 0 ? Math.abs(val) : '' } }
            }
        });
    }
    // 8. Top chi nhánh doanh thu
    if (document.getElementById('hq-chart-topdt')) {
        new Chart(document.getElementById('hq-chart-topdt'), {
            type: 'bar',
            data: {
                labels: ['Hà Nội - Cầu Giấy', 'TP. Hồ Chí Minh - Q.3', 'Đà Nẵng - Hải Châu', 'Bình Dương - Thủ Dầu Một', 'Hải Phòng - Lê Chân'],
                datasets: [{
                    data: [0.92, 0.81, 0.68, 0.53, 0.47],
                    backgroundColor: colorPrimary,
                    borderRadius: 4
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                scales: { x: { display: false }, y: { grid: { display: false } } },
                plugins: { legend: { display: false }, datalabels: { display: true, anchor: 'end', align: 'end' } }
            }
        });
    }
    // 9. Top chi nhánh lợi nhuận
    if (document.getElementById('hq-chart-topln')) {
        new Chart(document.getElementById('hq-chart-topln'), {
            type: 'bar',
            data: {
                labels: ['Hà Nội - Cầu Giấy', 'TP. Hồ Chí Minh - Q.3', 'Đà Nẵng - Hải Châu', 'Bình Dương - Thủ Dầu Một', 'Hải Phòng - Lê Chân'],
                datasets: [{
                    data: [0.32, 0.31, 0.28, 0.23, 0.17],
                    backgroundColor: colorPrimary,
                    borderRadius: 4
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                scales: { x: { display: false }, y: { grid: { display: false } } },
                plugins: { legend: { display: false }, datalabels: { display: true, anchor: 'end', align: 'end' } }
            }
        });
    }
}
function initRuiRoTab() {
    const colorPrimary = '#005a32';
    const colorOrange = '#f97316';
    const colorRed = '#ef4444';
    const colorGreen = '#10b981';
    const colorYellow = '#f59e0b';
    const colorGray = '#9ca3af';
    // 2. Radar 5 nhóm nợ
    if (document.getElementById('rr-chart-radar')) {
        new Chart(document.getElementById('rr-chart-radar'), {
            type: 'radar',
            data: {
                labels: ['Nhóm 1', 'Nhóm 2', 'Nhóm 3', 'Nhóm 4', 'Nhóm 5'],
                datasets: [
                    {
                        label: 'Tỷ lệ nợ xấu',
                        data: [65, 59, 90, 81, 56],
                        backgroundColor: 'rgba(0, 90, 50, 0.2)',
                        borderColor: colorPrimary,
                        pointBackgroundColor: colorPrimary,
                    },
                    {
                        label: 'Tỷ lệ nợ xấu cùng kỳ',
                        data: [28, 48, 40, 19, 96],
                        backgroundColor: 'rgba(156, 163, 175, 0.2)',
                        borderColor: colorGray,
                        pointBackgroundColor: colorGray,
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { 
                    legend: { 
                        position: 'right', 
                        labels: { 
                            boxWidth: 8, 
                            usePointStyle: true, 
                            font: { size: 9 },
                            padding: 10
                        } 
                    }, 
                    datalabels: { display: false } 
                },
                scales: { 
                    r: { 
                        ticks: { display: false },
                        pointLabels: {
                            font: {
                                size: 10,
                                weight: '600'
                            }
                        }
                    } 
                }
            }
        });
    }
    // 3. Phân bổ nguyên nhân nợ xấu
    if (document.getElementById('rr-chart-nguyennhan')) {
        new Chart(document.getElementById('rr-chart-nguyennhan'), {
            type: 'doughnut',
            data: {
                labels: ['Chậm chuyển tiền', 'Hoàn xuất cảnh', 'Mất việc', 'Quên lịch trả', 'Khác'],
                datasets: [{
                    data: [32.4, 22.1, 18.6, 16.3, 10.6],
                    backgroundColor: [colorPrimary, colorOrange, colorYellow, colorGreen, colorGray],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '60%',
                plugins: {
                    legend: { position: 'right', labels: { boxWidth: 10, usePointStyle: true, font: { size: 10 } } },
                    datalabels: { display: false }
                }
            }
        });
    }
    // 4. Xu hướng nợ xấu
    if (document.getElementById('rr-chart-xuhuong')) {
        new Chart(document.getElementById('rr-chart-xuhuong'), {
            type: 'line',
            data: {
                labels: Array.from({ length: 12 }, (_, i) => `T${i + 1}`),
                datasets: [
                    {
                        label: 'Tỷ lệ nợ xấu (%)',
                        data: [8.2, 8.5, 8.1, 7.8, 7.4, 7.1, 6.9, 6.8, 6.6, 6.4, 6.3, 6.2],
                        borderColor: colorPrimary,
                        backgroundColor: colorPrimary,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Tỷ lệ thu hồi (%)',
                        data: [64.5, 64.8, 65.7, 66.3, 66.9, 68.0, 69.1, 69.4, 70.2, 70.8, 71.6, 72.4],
                        borderColor: colorOrange,
                        backgroundColor: colorOrange,
                        yAxisID: 'y1'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'top', labels: { boxWidth: 10, usePointStyle: true } }, datalabels: { display: true, align: 'top', font: { size: 9 } } },
                scales: {
                    x: { grid: { display: false } },
                    y: { position: 'left', min: 0, max: 20 },      /* Increased max to push the line down */
                    y1: { position: 'right', min: 30, max: 85, grid: { display: false } } /* Narrowed range to push the line up */
                }
            }
        });
    }
    // 5. Nợ xấu theo tỉnh thành
    if (document.getElementById('rr-chart-noxautinh')) {
        const ctxNoxau = document.getElementById('rr-chart-noxautinh');
        const dataTinh = [12.7, 11.2, 10.6, 9.3, 8.1, 7.2, 6.4, 5.7];
        const labelsTinh = ['Thanh Hóa', 'Nghệ An', 'Hải Phòng', 'Bình Dương', 'Đà Nẵng', 'Đồng Nai', 'Cần Thơ', 'Hà Nội'];
        
        const dataChiNhanh = [14.2, 12.8, 11.5, 10.2, 9.8, 8.5, 7.9, 6.2];
        const labelsChiNhanh = ['CN Thanh Hóa 1', 'CN Vinh 2', 'CN Hải An', 'CN Thuận An', 'CN Liên Chiểu', 'CN Biên Hòa', 'CN Ninh Kiều', 'CN Cầu Giấy'];

        const chartNoxau = new Chart(ctxNoxau, {
            type: 'bar',
            data: {
                labels: labelsTinh,
                datasets: [{
                    data: dataTinh,
                    backgroundColor: (ctx) => ctx.dataIndex === 0 ? colorRed : colorPrimary,
                    borderRadius: 4
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                scales: { x: { display: false }, y: { grid: { display: false }, ticks: { font: { size: 9 } } } },
                plugins: { legend: { display: false }, datalabels: { display: true, anchor: 'end', align: 'end', font: { size: 9 } } }
            }
        });

        // Toggle logic
        const toggleBtns = ctxNoxau.closest('.card').querySelectorAll('.toggle-btn');
        toggleBtns.forEach((btn, index) => {
            btn.addEventListener('click', () => {
                toggleBtns.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                
                if (index === 0) { // Tỉnh thành
                    chartNoxau.data.labels = labelsTinh;
                    chartNoxau.data.datasets[0].data = dataTinh;
                } else { // Chi nhánh
                    chartNoxau.data.labels = labelsChiNhanh;
                    chartNoxau.data.datasets[0].data = dataChiNhanh;
                }
                chartNoxau.update();
            });
        });
    }
    // 6. Nợ xấu theo kênh
    if (document.getElementById('rr-chart-noxaukenh')) {
        new Chart(document.getElementById('rr-chart-noxaukenh'), {
            type: 'bar',
            data: {
                labels: ['10+', '90+', '180+', '360+', '>360'],
                datasets: [
                    {
                        label: 'Tại chi nhánh',
                        data: [63.1, 61.4, 59.3, 58.0, 56.2],
                        backgroundColor: colorPrimary
                    },
                    {
                        label: 'Qua App',
                        data: [36.9, 38.6, 40.7, 42.0, 43.8],
                        backgroundColor: colorOrange
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { stacked: true, grid: { display: false } },
                    y: { stacked: true, display: false }
                },
                plugins: { legend: { position: 'top', labels: { boxWidth: 10, usePointStyle: true, font: { size: 10 } } }, datalabels: { display: true, color: '#fff', font: { size: 9 }, formatter: val => val + '%' } }
            }
        });
    }
    // 7. Thu hồi vốn theo bucket nợ
    if (document.getElementById('rr-chart-thuhoi')) {
        new Chart(document.getElementById('rr-chart-thuhoi'), {
            type: 'bar',
            data: {
                labels: ['10+', '90+', '180+', '360+', '>360'],
                datasets: [{
                    data: [85.6, 78.2, 60.2, 45.1, 26.7],
                    backgroundColor: colorPrimary,
                    borderRadius: 4
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                scales: { x: { display: false, max: 100 }, y: { grid: { display: false } } },
                plugins: { legend: { display: false }, datalabels: { display: true, anchor: 'end', align: 'end', formatter: val => val + '%', font: { size: 9 } } }
            }
        });
    }
    // 8. Tỷ lệ xóa nợ theo tháng
    if (document.getElementById('rr-chart-xoano')) {
        new Chart(document.getElementById('rr-chart-xoano'), {
            type: 'bar',
            data: {
                labels: Array.from({ length: 12 }, (_, i) => `T${i + 1}`),
                datasets: [{
                    data: [1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.7, 1.9, 2.0, 2.0, 2.1, 2.2],
                    backgroundColor: colorOrange,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: { x: { grid: { display: false } }, y: { display: false } },
                plugins: { legend: { display: false }, datalabels: { display: true, align: 'top', anchor: 'end', font: { size: 9 } } }
            }
        });
    }
}
function initChanDungTab() {
    const colorPrimary = '#005a32';
    const colorOrange = '#f97316';
    const colorRed = '#ef4444';
    const colorGreen = '#10b981';
    const colorYellow = '#f59e0b';
    const colorGray = '#9ca3af';
    // Helper for donut charts with 2-line legend
    const createDonut = (id, labels, data, legendId) => {
        if (!document.getElementById(id)) return;
        const colors = [colorPrimary, colorOrange, colorGreen, colorYellow, colorGray, colorRed];
        new Chart(document.getElementById(id), {
            type: 'doughnut',
            data: {
                labels: labels,
                datasets: [{
                    data: data,
                    backgroundColor: colors,
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '65%',
                plugins: {
                    legend: { display: false },
                    datalabels: { display: false }
                }
            }
        });

        // Generate Grid Legend (2 columns)
        const legendContainer = document.getElementById(legendId);
        if (legendContainer) {
            legendContainer.innerHTML = labels.map((label, i) => `
                <div class="legend-item">
                    <span class="legend-dot" style="background-color: ${colors[i % colors.length]}"></span>
                    <span>${label}</span>
                </div>
            `).join('');
        }
    };

    // 1-4 Donuts
    createDonut('cd-chart-kenh', ['Chi nhánh', 'App', 'Website', 'Telesales'], [68.3, 31.7, 5.8, 1.4], 'legend-kenh');
    createDonut('cd-chart-gioitinh', ['Nam', 'Nữ'], [60.8, 39.2], 'legend-gioitinh');
    createDonut('cd-chart-khuvuc', ['Miền Bắc', 'Miền Trung', 'Miền Nam', 'Tây Nguyên', 'Đông Nam Bộ'], [42.3, 18.4, 30.1, 4.7, 4.5], 'legend-khuvuc');
    createDonut('cd-chart-tinhtrang', ['Đang vay', 'Đã tất toán', 'Quá hạn', 'Khác'], [45.2, 52.3, 4.1, 0.4], 'legend-tinhtrang');
    // 5. Độ tuổi
    if (document.getElementById('cd-chart-dotuoi')) {
        new Chart(document.getElementById('cd-chart-dotuoi'), {
            type: 'bar',
            data: {
                labels: ['18-24', '25-34', '35-44', '45-54', '55-64', '>64'],
                datasets: [{
                    data: [8.2, 32.4, 28.7, 18.9, 9.1, 2.7],
                    backgroundColor: colorPrimary,
                    borderRadius: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: { x: { grid: { display: false }, ticks: { font: { size: 9 } } }, y: { display: false } },
                plugins: { legend: { display: false }, datalabels: { display: true, align: 'top', anchor: 'end', formatter: val => val + '%', font: { size: 9 } } }
            }
        });
    }
    // 6. Nghề nghiệp
    if (document.getElementById('cd-chart-nghenghiep')) {
        new Chart(document.getElementById('cd-chart-nghenghiep'), {
            type: 'bar',
            data: {
                labels: ['Công nhân', 'Kinh doanh tự do', 'Nhân viên công ty', 'Nông nghiệp', 'Nội trợ', 'Khác'],
                datasets: [{
                    data: [28.1, 25.4, 18.7, 12.6, 9.5, 5.7],
                    backgroundColor: colorPrimary,
                    borderRadius: 4
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                scales: { x: { display: false }, y: { grid: { display: false }, ticks: { font: { size: 9 } } } },
                plugins: { legend: { display: false }, datalabels: { display: true, anchor: 'end', align: 'end', formatter: val => val + '%', font: { size: 9 } } }
            }
        });
    }
    // 7. Xu hướng khách hàng mới
    if (document.getElementById('cd-chart-xuhuong')) {
        new Chart(document.getElementById('cd-chart-xuhuong'), {
            type: 'line',
            data: {
                labels: Array.from({ length: 12 }, (_, i) => `T${i + 1}`),
                datasets: [
                    {
                        label: 'Năm nay',
                        data: [20, 25, 28, 30, 35, 32, 38, 40, 42, 45, 48, 50],
                        borderColor: colorPrimary,
                        backgroundColor: colorPrimary,
                        tension: 0.3
                    },
                    {
                        label: 'Năm trước',
                        data: [18, 22, 24, 25, 28, 26, 30, 32, 35, 38, 40, 42],
                        borderColor: 'rgba(156, 163, 175, 0.5)',
                        borderDash: [5, 5],
                        backgroundColor: 'transparent',
                        tension: 0.3
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'top', labels: { boxWidth: 10, usePointStyle: true, font: { size: 10 } } }, datalabels: { display: false } },
                scales: { x: { grid: { display: false } }, y: { display: false } }
            }
        });
    }
    // 8. Phân bổ mức khoản vay
    if (document.getElementById('cd-chart-mucvay')) {
        new Chart(document.getElementById('cd-chart-mucvay'), {
            type: 'bar',
            data: {
                labels: ['3-10tr', '10-30tr', '30-50tr', '50-100tr', '100-300tr', '300-500tr', '500tr-1ty', '1tỷ-2ty', '>2ty'],
                datasets: [{
                    data: [15.2, 28.5, 18.7, 12.8, 9.5, 6.2, 4.3, 3.1, 1.7],
                    backgroundColor: colorPrimary,
                    borderRadius: 4
                }]
            },
            options: {
                indexAxis: 'y', // Change to horizontal for long labels
                responsive: true,
                maintainAspectRatio: false,
                scales: { 
                    x: { display: false }, 
                    y: { grid: { display: false }, ticks: { font: { size: 9 } } } 
                },
                plugins: { 
                    legend: { display: false }, 
                    datalabels: { 
                        display: true, 
                        anchor: 'end', 
                        align: 'end', 
                        formatter: val => val + '%', 
                        font: { size: 9 } 
                    } 
                }
            }
        });
    }
}