// js/realtime/charts.js

function initRealtimeCharts() {
    new Chart(document.getElementById('dailyStatusBar').getContext('2d'), {
        type: 'bar',
        data: {
            labels: ['Quá hạn', 'Chấp thuận', 'Từ chối'],
            datasets: [{
                data: [45, 210, 32],
                backgroundColor: ['#ffc20e', '#00a651', '#ef4444'],
                borderRadius: 4
            }]
        },
        options: {
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true, ticks: { font: { size: 9 } } }, x: { ticks: { font: { size: 9 } } } }
        }
    });

    new Chart(document.getElementById('customerProductDoughnut').getContext('2d'), {
        type: 'doughnut',
        data: { 
            labels: ['Mới (XM)', 'Cũ (XM)', 'Mới (Ô tô)', 'Cũ (Ô tô)'], 
            datasets: [{ 
                data: [120, 350, 45, 110], 
                backgroundColor: ['#00a651', '#34d399', '#3b82f6', '#93c5fd'], 
                borderWidth: 0 
            }] 
        },
        options: { 
            cutout: '55%', 
            plugins: { 
                legend: { position: 'bottom', labels: { boxWidth: 8, font: { size: 9 }, padding: 6 } }, 
                centerText: { mainText: '625', subText: 'Hồ sơ' } 
            } 
        }
    });

    new Chart(document.getElementById('realtimeLineChart').getContext('2d'), {
        type: 'line',
        data: {
            labels: ['08:00','09:00','10:00','11:00','12:00','13:00','14:00','15:00'],
            datasets: [
                { label: 'Giải ngân', data: [12,25,45,60,20,30,42,55], borderColor: '#00a651', backgroundColor: 'rgba(0, 166, 81, 0.1)', borderWidth: 2, fill: true, tension: 0.4 },
                { label: 'Thu nợ', data: [8,15,22,35,40,25,30,48], borderColor: '#ffc20e', backgroundColor: 'rgba(255, 194, 14, 0.1)', borderWidth: 2, fill: true, tension: 0.4 }
            ]
        },
        options: { 
            plugins: { 
                legend: { position: 'top' },
                tooltip: { callbacks: { label: function(context) { return context.dataset.label + ': ' + currencyFormatter(context.parsed.y); } } }
            }, 
            scales: { y: { beginAtZero: true, ticks: { callback: function(value) { return value + 'M'; } } } } 
        }
    });

    new Chart(document.getElementById('riskRadarChart').getContext('2d'), {
        type: 'radar',
        data: {
            labels: ['Thời tiết', 'Kẹt xe', 'Hụt thu', 'DTI cao', 'LTV cao', 'Fraud'],
            datasets: [{
                label: 'Rủi ro',
                data: [90, 75, 80, 50, 45, 20],
                backgroundColor: 'rgba(239, 68, 68, 0.2)',
                borderColor: '#ef4444',
                pointBackgroundColor: '#ef4444'
            }]
        },
        options: { scales: { r: { angleLines: { color: 'rgba(255,255,255,0.1)' }, grid: { color: 'rgba(255,255,255,0.1)' }, pointLabels: { font: {size: 9} }, ticks: { display: false, min: 0, max: 100 } } }, plugins: { legend: { display: false } } }
    });
}
