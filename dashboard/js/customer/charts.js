// js/customer/charts.js

function initCustomerCharts() {
    // 1. Phân bổ Thu nhập theo Nhóm Rủi ro (Stacked Bar)
    new Chart(document.getElementById('incomeRiskStackedBar').getContext('2d'), {
        type: 'bar',
        data: {
            labels: ['< 5tr', '5-10tr', '10-20tr', '20-50tr', '> 50tr'],
            datasets: [
                { label: 'Rủi ro thấp', data: [15, 35, 55, 30, 10], backgroundColor: '#00a651' },
                { label: 'Rủi ro trung bình', data: [25, 45, 30, 15, 5], backgroundColor: '#f59e0b' },
                { label: 'Rủi ro cao', data: [40, 20, 15, 5, 2], backgroundColor: '#ef4444' }
            ]
        },
        options: {
            indexAxis: 'y',
            scales: {
                x: { stacked: true, grid: { color: 'rgba(255,255,255,0.05)' } },
                y: { stacked: true, grid: { display: false } }
            },
            plugins: {
                legend: { position: 'bottom', labels: { boxWidth: 12, color: '#94a3b8' } }
            }
        }
    });

    // 2. Tuổi vs Thu nhập (Bubble, màu theo PAR)
    new Chart(document.getElementById('ageIncomeBubblePAR').getContext('2d'), {
        type: 'bubble',
        data: {
            datasets: [
                { 
                    label: 'PAR < 5%', 
                    data: [{x: 35, y: 35, r: 12}, {x: 40, y: 45, r: 15}, {x: 45, y: 55, r: 10}], 
                    backgroundColor: 'rgba(0, 166, 81, 0.6)', borderColor: '#fff' 
                },
                { 
                    label: 'PAR 5-15%', 
                    data: [{x: 28, y: 25, r: 18}, {x: 32, y: 30, r: 12}], 
                    backgroundColor: 'rgba(245, 158, 11, 0.6)', borderColor: '#fff' 
                },
                { 
                    label: 'PAR > 15%', 
                    data: [{x: 22, y: 15, r: 20}, {x: 25, y: 20, r: 15}], 
                    backgroundColor: 'rgba(239, 68, 68, 0.6)', borderColor: '#fff' 
                }
            ]
        },
        options: {
            scales: {
                x: { title: { display: true, text: 'Độ tuổi', color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                y: { title: { display: true, text: 'Thu nhập (Triệu)', color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } }
            },
            plugins: {
                legend: { position: 'bottom', labels: { boxWidth: 10, font: { size: 10 }, color: '#94a3b8' } },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `Tuổi: ${context.raw.x}, TN: ${context.raw.y}tr, Quy mô: ${context.raw.r} tỷ`;
                        }
                    }
                }
            }
        }
    });

    // 3. Nghề nghiệp vs PAR Rate (Horizontal Bar)
    new Chart(document.getElementById('jobPARHBar').getContext('2d'), {
        type: 'bar',
        data: {
            labels: ['Tài xế công nghệ', 'Công nhân', 'NV Văn phòng', 'Tiểu thương', 'Sinh viên'],
            datasets: [{
                label: 'Tỷ lệ PAR 30+ (%)',
                data: [8.5, 6.2, 2.1, 4.5, 12.4],
                backgroundColor: function(context) {
                    const value = context.dataset.data[context.dataIndex];
                    return value > 8 ? '#ef4444' : value > 4 ? '#f59e0b' : '#00a651';
                },
                borderRadius: 4
            }]
        },
        options: {
            indexAxis: 'y',
            plugins: { legend: { display: false } },
            scales: { x: { ticks: { callback: v => v + '%' }, grid: { color: 'rgba(255,255,255,0.05)' } } }
        }
    });

    // 5. Phân bổ Credit Score (Histogram)
    new Chart(document.getElementById('creditScoreHistogram').getContext('2d'), {
        type: 'bar',
        data: {
            labels: ['300-400', '400-500', '500-600', '600-700', '700-800', '800-850'],
            datasets: [{
                label: 'Số lượng KH',
                data: [120, 450, 1200, 1850, 600, 150],
                backgroundColor: '#3b82f6',
                borderRadius: 4
            }]
        },
        options: {
            plugins: { legend: { display: false } },
            scales: {
                y: { grid: { color: 'rgba(255,255,255,0.05)' } },
                x: { grid: { display: false } }
            }
        }
    });
}

