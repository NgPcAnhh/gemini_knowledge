// js/risk/charts.js

function initRiskCharts() {
    // 1. Vintage Analysis
    new Chart(document.getElementById('vintageLineChart').getContext('2d'), {
        type: 'line',
        data: {
            labels: ['Tháng 1', 'Tháng 2', 'Tháng 3', 'Tháng 4', 'Tháng 5'],
            datasets: [
                { label: 'Nhóm T1', data: [1.2, 2.5, 3.8, 4.1, 4.5], borderColor: '#3b82f6', tension: 0.3, borderWidth: 2 },
                { label: 'Nhóm T2 (Leo dốc)', data: [0, 1.5, 3.0, 4.2, 5.8], borderColor: '#ef4444', tension: 0.3, borderWidth: 4, pointRadius: 5 },
                { label: 'Nhóm T3', data: [0, 0, 1.1, 2.3, 3.1], borderColor: '#00a651', tension: 0.3, borderWidth: 2 },
                { 
                    label: 'Ngưỡng an toàn (3%)', 
                    data: [3, 3, 3, 3, 3], 
                    borderColor: 'rgba(255, 255, 255, 0.2)', 
                    borderDash: [5, 5], 
                    pointRadius: 0, 
                    fill: false,
                    borderWidth: 1
                }
            ]
        },
        options: { 
            plugins: { 
                tooltip: { callbacks: { label: function(context) { return context.dataset.label + ': ' + context.parsed.y + '%'; } } },
                legend: { labels: { boxWidth: 12, font: { size: 10 } } }
            },
            scales: { y: { ticks: { callback: function(value) { return value + '%'; } }, grid: { color: 'rgba(255,255,255,0.05)' } } }
        }
    });

    // 2. Roll Rate Matrix (Heatmap Table)
    const rollRateContainer = document.getElementById('rollRateContainer');
    if (rollRateContainer) {
        rollRateContainer.innerHTML = `
            <div style="margin-bottom: 8px; font-size: 10px; color: var(--text-muted); font-style: italic;">
                * Cách đọc: Một khách hàng ở nhóm "Từ" (hàng) có bao nhiêu % xác suất chuyển sang nhóm "Đến" (cột) trong kỳ tiếp theo.
            </div>
            <table style="width: 100%; height: calc(100% - 25px); border-collapse: separate; border-spacing: 4px; font-size: 11px; table-layout: fixed;">
                <thead>
                    <tr style="color: var(--text-muted); height: 30px;">
                        <th style="width: 18%; text-align: left;">Từ \\ Đến</th>
                        <th style="text-align: center;">Trong hạn</th>
                        <th style="text-align: center;">1-30 ngày</th>
                        <th style="text-align: center;">31-90 ngày</th>
                        <th style="text-align: center;">Nợ xấu (M3+)</th>
                    </tr>
                </thead>
                <tbody style="font-weight: 500; text-align: center;">
                    <tr style="height: auto;">
                        <td style="color: var(--text-muted); font-weight: bold; text-align: left;">Trong hạn</td>
                        <td style="background: rgba(0,166,81,0.6); border-radius: 4px; color: white;" title="Duy trì trạng thái tốt">92%</td>
                        <td style="background: rgba(245,158,11,0.2); border-radius: 4px;" title="Chậm thanh toán nhẹ">6.5%</td>
                        <td style="background: rgba(239,68,68,0.1); border-radius: 4px;">1.2%</td>
                        <td style="border-radius: 4px;">0.3%</td>
                    </tr>
                    <tr style="height: auto;">
                        <td style="color: var(--text-muted); font-weight: bold; text-align: left;">1-30 ngày</td>
                        <td style="background: rgba(0,166,81,0.2); border-radius: 4px;" title="Cure rate (về nợ tốt)">15%</td>
                        <td style="background: rgba(0,166,81,0.6); border-radius: 4px; color: white;">72%</td>
                        <td style="background: rgba(245,158,11,0.3); border-radius: 4px;" title="Chuyển nhóm nợ 2">12%</td>
                        <td style="background: rgba(239,68,68,0.1); border-radius: 4px;">1%</td>
                    </tr>
                    <tr style="height: auto;">
                        <td style="color: var(--text-muted); font-weight: bold; text-align: left;">31-90 ngày</td>
                        <td style="border-radius: 4px;">2%</td>
                        <td style="background: rgba(0,166,81,0.2); border-radius: 4px;">8%</td>
                        <td style="background: rgba(0,166,81,0.5); border-radius: 4px; color: white;">65%</td>
                        <td style="background: rgba(239,68,68,0.5); border-radius: 4px; border: 2px solid var(--danger); font-weight: 800; color: #fff;" title="Điểm rò rỉ nợ xấu cao nhất!">25%</td>
                    </tr>
                    <tr style="height: auto;">
                        <td style="color: var(--text-muted); font-weight: bold; text-align: left;">Nợ xấu</td>
                        <td style="border-radius: 4px;">0%</td>
                        <td style="border-radius: 4px;">1%</td>
                        <td style="background: rgba(0,166,81,0.2); border-radius: 4px;">5%</td>
                        <td style="background: rgba(0,166,81,0.8); border-radius: 4px; color: white;">94%</td>
                    </tr>
                </tbody>
            </table>
        `;
    }

    // 3. Nợ xấu theo Quận
    new Chart(document.getElementById('riskHBarChart').getContext('2d'), {
        type: 'bar',
        data: { 
            labels: ['Bình Thạnh', 'Gò Vấp', 'Thủ Đức', 'Quận 1'], 
            datasets: [
                { 
                    label: 'Tỷ lệ Quá hạn %', 
                    data: [12, 8, 5, 2], 
                    backgroundColor: function(context) {
                        const value = context.dataset.data[context.dataIndex];
                        return value > 10 ? '#ef4444' : value > 6 ? '#f59e0b' : '#00a651';
                    },
                    borderRadius: 4,
                    barThickness: 20
                },
                {
                    label: 'Trung bình (5.2%)',
                    data: [5.2, 5.2, 5.2, 5.2],
                    type: 'line',
                    borderColor: 'rgba(255, 255, 255, 0.4)',
                    borderDash: [5, 5],
                    pointRadius: 0,
                    fill: false
                }
            ] 
        },
        options: { 
            indexAxis: 'y', 
            plugins: { legend: { display: false } }, 
            scales: { x: { ticks: { callback: function(value) { return value + '%'; } }, grid: { color: 'rgba(255,255,255,0.05)' } } } 
        }
    });

    // 4. Cấu trúc Rủi ro
    new Chart(document.getElementById('riskTypePie').getContext('2d'), {
        type: 'pie',
        data: { 
            labels: ['Mất khả năng trả', 'Lừa đảo', 'Quên lịch', 'Khác'], 
            datasets: [{ 
                data: [50, 15, 30, 5], 
                backgroundColor: ['#ef4444', '#9333ea', '#f59e0b', '#6b7280'], 
                borderWidth: 2,
                borderColor: '#111827',
                hoverOffset: 15
            }] 
        },
        options: { 
            plugins: { 
                legend: { 
                    position: 'right',
                    labels: {
                        color: '#ffffff',
                        font: { size: 10 },
                        generateLabels: function(chart) {
                            const data = chart.data;
                            return data.labels.map((label, i) => {
                                const value = data.datasets[0].data[i];
                                const total = data.datasets[0].data.reduce((a, b) => a + b, 0);
                                const percentage = ((value / total) * 100).toFixed(0) + '%';
                                let extra = '';
                                if (label === 'Quên lịch') extra = ' (Quick Win!)';
                                return {
                                    text: `${label}: ${percentage} (${value} hồ sơ)${extra}`,
                                    fillStyle: data.datasets[0].backgroundColor[i],
                                    fontColor: '#ffffff',
                                    color: '#ffffff',
                                    hidden: false,
                                    index: i
                                };
                            });
                        }
                    }
                } 
            } 
        }
    });

    // 5. Phân tán LTV vs Thu Nhập
    new Chart(document.getElementById('riskBubbleChart').getContext('2d'), {
        type: 'bubble',
        data: {
            datasets: [{
                label: 'Nhóm khách hàng',
                data: [
                    {x: 400, y: 55, r: 8, name: 'Công nhân KCN'}, 
                    {x: 450, y: 48, r: 12, name: 'NV Văn phòng'}, 
                    {x: 600, y: 35, r: 8, name: 'Chủ hộ kinh doanh'}, 
                    {x: 350, y: 65, r: 10, name: 'App Driver (Rủi ro)'}, 
                    {x: 550, y: 30, r: 5, name: 'Sinh viên'}
                ],
                backgroundColor: function(context) {
                    const y = context.raw ? context.raw.y : 0;
                    return y > 60 ? 'rgba(239, 68, 68, 0.6)' : 'rgba(59, 130, 246, 0.6)';
                },
                borderColor: '#fff',
                borderWidth: 1
            }]
        },
        options: { 
            plugins: { 
                legend: { display: false }, 
                tooltip: { 
                    callbacks: { 
                        label: function(context) { 
                            const raw = context.raw;
                            return [
                                `Nhóm: ${raw.name}`,
                                `Thu nhập: ${raw.x}K VNĐ`,
                                `LTV: ${raw.y}%`,
                                `Dư nợ: ${raw.r * 10} tỷ`
                            ];
                        } 
                    } 
                } 
            },
            scales: { 
                x: { 
                    title: { display: true, text: 'Thu nhập (K)', color: '#94a3b8', font: { size: 10 } },
                    min: 200, max: 800, 
                    ticks: { callback: function(value) { return value + 'K'; } },
                    grid: { color: 'rgba(255,255,255,0.05)' }
                }, 
                y: { 
                    title: { display: true, text: 'LTV (%)', color: '#94a3b8', font: { size: 10 } },
                    min: 20, max: 80, 
                    ticks: { callback: function(value) { return value + '%'; } },
                    grid: { color: 'rgba(255,255,255,0.05)' }
                } 
            }
        }
    });
}

