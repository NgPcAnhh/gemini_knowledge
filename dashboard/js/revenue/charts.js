// js/revenue/charts.js

function initRevenueCharts() {
    // Ticket Size Distribution
    new Chart(document.getElementById('ticketSizeDistribution').getContext('2d'), {
        type: 'doughnut',
        data: {
            labels: ['Nhỏ', 'Vừa', 'Lớn'],
            datasets: [{
                data: [45, 35, 20],
                backgroundColor: ['#00a651', '#f59e0b', '#ef4444'],
                borderWidth: 0
            }]
        },
        options: {
            cutout: '60%',
            layout: { padding: { top: 35, left: 35, right: 35, bottom: 0 } },
            plugins: {
                legend: { position: 'bottom', labels: { font: { size: 12, weight: 'bold' }, padding: 12, color: '#ffffff' } },
                centerText: { mainText: '18.4K', subText: '', fontSize: 20 }
            }
        }
    });

    // Average Loan Size & Disbursement Combo
    new Chart(document.getElementById('avgLoanSizeCombo').getContext('2d'), {
        type: 'bar',
        data: {
            labels: ['T1', 'T2', 'T3', 'T4', 'T5'],
            datasets: [
                {
                    type: 'line',
                    label: 'Quy mô TB (ngàn)',
                    data: [450, 465, 480, 490, 473],
                    borderColor: '#00a651',
                    yAxisID: 'y1',
                    tension: 0.4,
                    pointRadius: 4,
                    pointBackgroundColor: '#00a651'
                },
                {
                    type: 'bar',
                    label: 'Giải ngân (tỷ)',
                    data: [420, 580, 650, 720, 480],
                    backgroundColor: '#ffc20e',
                    borderRadius: 4,
                    yAxisID: 'y'
                }
            ]
        },
        options: {
            scales: {
                y: { position: 'left', ticks: { callback: function (value) { return value + 'M'; } } },
                y1: { position: 'right', grid: { drawOnChartArea: false }, ticks: { callback: function (value) { return value + 'K'; } } }
            },
            plugins: { tooltip: { callbacks: { label: function (context) { return context.dataset.label + ': ' + context.parsed.y; } } } }
        }
    });

    // Cost of Fund vs Yield on Portfolio
    new Chart(document.getElementById('costYieldComparison').getContext('2d'), {
        type: 'line',
        data: {
            labels: ['T1', 'T2', 'T3', 'T4', 'T5'],
            datasets: [
                { label: 'Chi phí vốn (%)', data: [6.2, 6.5, 6.1, 6.3, 6.2], borderColor: '#f59e0b', backgroundColor: 'rgba(245, 158, 11, 0.1)', fill: true, tension: 0.3 }
            ]
        },
        options: {
            scales: { y: { ticks: { callback: function (value) { return value + '%'; } } } },
            plugins: { tooltip: { callbacks: { label: function (context) { return context.dataset.label + ': ' + context.parsed.y + '%'; } } } }
        }
    });

    // Net Revenue per Loan
    new Chart(document.getElementById('netRevenuePerLoan').getContext('2d'), {
        type: 'bar',
        data: {
            labels: ['T1', 'T2', 'T3', 'T4', 'T5'],
            datasets: [{
                label: 'Doanh thu / HĐ (ngàn)',
                data: [78, 82, 87, 85, 88],
                backgroundColor: '#3b82f6',
                borderRadius: 4,
                borderWidth: 0
            }]
        },
        options: {
            plugins: { legend: { display: false }, tooltip: { callbacks: { label: function (context) { return context.parsed.y + 'K VND'; } } } },
            scales: { y: { ticks: { callback: function (value) { return value + 'K'; } } } }
        }
    });

    // Loan Growth Rate Timeline
    new Chart(document.getElementById('loanGrowthTimeline').getContext('2d'), {
        type: 'line',
        data: {
            labels: ['5/2024', '6/2024', '7/2024', '8/2024', '9/2024', '10/2024', '11/2024', '12/2024', '1/2025', '2/2025', '3/2025', '4/2025', '5/2025'],
            datasets: [{
                label: 'Tốc độ Tăng trưởng (%)',
                data: [8.2, 9.1, 10.5, 11.2, 11.8, 12.1, 12.0, 11.9, 12.5, 12.8, 12.3, 12.1, 12.3],
                borderColor: '#00a651',
                backgroundColor: 'rgba(0, 166, 81, 0.1)',
                fill: true,
                tension: 0.3,
                pointRadius: 3,
                pointBackgroundColor: '#00a651'
            }]
        },
        options: {
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        title: function (context) { return 'Tháng: ' + context[0].label; },
                        label: function (context) { return 'Tăng trưởng: ' + context.parsed.y + '% (YoY)'; }
                    }
                }
            },
            scales: { y: { ticks: { callback: function (value) { return value + '%'; } } } }
        }
    });

    // Outstanding Loan Distribution
    new Chart(document.getElementById('outstandingLoanPie').getContext('2d'), {
        type: 'pie',
        data: {
            labels: ['Hoạt động', 'Chuẩn bị đóng', 'Đã tất toán'],
            datasets: [{
                data: [75, 18, 7],
                backgroundColor: ['#00a651', '#ffc20e', '#6b7280'],
                borderWidth: 0
            }]
        },
        options: {
            plugins: { legend: { position: 'bottom', labels: { font: { size: 9 } } } }
        }
    });
}
