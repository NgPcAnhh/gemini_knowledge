// js/realtime/charts.js

function destroyRealtimeCharts() {
    if (!window.realtimeCharts) return;
    Object.values(window.realtimeCharts).forEach(chart => {
        if (chart && typeof chart.destroy === 'function') {
            try { chart.destroy(); } catch (_) {}
        }
    });
    window.realtimeCharts = null;
}

function initRealtimeCharts() {
    destroyRealtimeCharts();

    const statusCanvas = document.getElementById('dailyStatusBar');
    const productCanvas = document.getElementById('customerProductDoughnut');
    const lineCanvas = document.getElementById('realtimeLineChart');
    const radarCanvas = document.getElementById('riskRadarChart');

    if (!statusCanvas || !productCanvas || !lineCanvas || !radarCanvas) return;

    const statusChart = new Chart(statusCanvas.getContext('2d'), {
        type: 'bar',
        data: {
            labels: ['Quá hạn', 'Chấp thuận', 'Từ chối'],
            datasets: [{ data: [0, 0, 0], backgroundColor: ['#ffc20e', '#00a651', '#ef4444'], borderRadius: 4 }]
        },
        options: {
            animation: { duration: 250 },
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true, ticks: { font: { size: 9 } } }, x: { ticks: { font: { size: 9 } } } }
        }
    });

    const productChart = new Chart(productCanvas.getContext('2d'), {
        type: 'doughnut',
        data: {
            labels: ['Xe máy', 'Ô tô', 'Điện thoại/Laptop', 'Bất động sản', 'Không TSĐB/Khác'],
            datasets: [{ data: [0, 0, 0, 0, 0], backgroundColor: ['#00a651', '#34d399', '#3b82f6', '#93c5fd', '#64748b'], borderWidth: 0 }]
        },
        options: {
            animation: { duration: 250 },
            cutout: '55%',
            plugins: {
                legend: { position: 'bottom', labels: { boxWidth: 8, font: { size: 9 }, padding: 6 } },
                centerText: { mainText: '0', subText: 'Tài sản' }
            }
        }
    });

    const lineChart = new Chart(lineCanvas.getContext('2d'), {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                { label: 'Giải ngân', data: [], borderColor: '#00a651', backgroundColor: 'rgba(0, 166, 81, 0.1)', borderWidth: 2, fill: true, tension: 0.4 },
                { label: 'Thu nợ', data: [], borderColor: '#ffc20e', backgroundColor: 'rgba(255, 194, 14, 0.1)', borderWidth: 2, fill: true, tension: 0.4 }
            ]
        },
        options: {
            animation: { duration: 250 },
            plugins: { legend: { position: 'top' }, tooltip: { callbacks: { label: ctx => `${ctx.dataset.label}: ${ctx.parsed.y}M` } } },
            scales: { y: { beginAtZero: true, ticks: { callback: value => `${value}M` } } }
        }
    });

    const radarChart = new Chart(radarCanvas.getContext('2d'), {
        type: 'radar',
        data: {
            labels: ['Thời tiết', 'PAR 1+', 'Trả chậm', 'Reject DTI', 'Reject LTV', 'Fraud'],
            datasets: [{ label: 'Rủi ro', data: [0, 0, 0, 0, 0, 0], backgroundColor: 'rgba(239, 68, 68, 0.2)', borderColor: '#ef4444', pointBackgroundColor: '#ef4444' }]
        },
        options: {
            animation: { duration: 250 },
            scales: { r: { min: 0, max: 100, angleLines: { color: 'rgba(255,255,255,0.1)' }, grid: { color: 'rgba(255,255,255,0.1)' }, pointLabels: { font: { size: 9 } }, ticks: { display: false } } },
            plugins: { legend: { display: false } }
        }
    });

    window.realtimeCharts = { statusChart, productChart, lineChart, radarChart };

    if (window.latestRealtimePayload) updateRealtimeCharts(window.latestRealtimePayload);
}

function normalizeArray(values, length) {
    const arr = Array.isArray(values) ? values.slice(0, length) : [];
    while (arr.length < length) arr.push(0);
    return arr.map(v => Number(v || 0));
}

function updateRealtimeCharts(payload) {
    if (!window.realtimeCharts || !payload) return;

    const { statusChart, productChart, lineChart, radarChart } = window.realtimeCharts;

    if (payload.approval_bar && statusChart) {
        statusChart.data.datasets[0].data = normalizeArray(payload.approval_bar, 3);
        statusChart.update();
    }

    if (payload.product_mix && productChart) {
        const data = normalizeArray(payload.product_mix, 5);
        productChart.data.datasets[0].data = data;
        const total = data.reduce((sum, v) => sum + v, 0);
        if (productChart.options.plugins.centerText) productChart.options.plugins.centerText.mainText = String(total);
        productChart.update();
    }

    if (payload.hourly && lineChart) {
        lineChart.data.labels = payload.hourly.labels || [];
        lineChart.data.datasets[0].data = payload.hourly.disbursement || [];
        lineChart.data.datasets[1].data = payload.hourly.collection || [];
        lineChart.update();
    }

    if (payload.risk_radar && radarChart) {
        radarChart.data.datasets[0].data = normalizeArray(payload.risk_radar, 6);
        radarChart.update();
    }
}
