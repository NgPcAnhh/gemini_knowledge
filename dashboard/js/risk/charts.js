// js/risk/charts.js

async function initRiskCharts() {
    const API_BASE = window.F88_API_BASE || `${window.location.protocol}//${window.location.hostname}:8000`;

    // Clean up previous risk charts to avoid canvas reuse errors
    if (window.riskCharts) {
        Object.values(window.riskCharts).forEach(chart => {
            if (chart && typeof chart.destroy === 'function') chart.destroy();
        });
    }
    window.riskCharts = {};

    try {
        const res = await fetch(`${API_BASE}/api/dashboard/risk`, { cache: 'no-store' });
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        const data = await res.json();

        // 1. Update top cost & risk KPI card metrics
        if (data.kpis) {
            const kpis = data.kpis;
            const setText = (id, value) => {
                const el = document.getElementById(id);
                if (el) el.textContent = value;
            };

            setText('val-risk-par1', `${kpis.par1_pct}%`);
            setText('val-risk-par7', `${kpis.par7_pct}%`);
            setText('val-risk-par14', `${kpis.par14_pct}%`);
            setText('val-risk-par30', `${kpis.par30_pct}%`);
            setText('val-risk-par90', `${kpis.par90_pct}%`);
            setText('val-risk-par180', `${kpis.par180_pct}%`);
            setText('val-risk-writeoff', `${kpis.write_off_rate}%`);
            setText('val-risk-recovery', `${kpis.recovery_rate}%`);
            setText('val-risk-coverage', `${kpis.coverage_pct}%`);
            setText('val-risk-roll', `${kpis.roll_rate}%`);
            setText('val-risk-avg-ltv', `${kpis.avg_ltv}%`);
            setText('val-risk-concentration', `${kpis.concentration_risk}%`);
        }

        // 2. Vintage Analysis Line Chart
        const ctxVintage = document.getElementById('vintageLineChart');
        if (ctxVintage && data.vintage) {
            window.riskCharts.vintage = new Chart(ctxVintage.getContext('2d'), {
                type: 'line',
                data: {
                    labels: data.vintage.labels,
                    datasets: [
                        { label: 'Cohort Q1-2025', data: data.vintage.datasets[0].data, borderColor: '#3b82f6', tension: 0.3, borderWidth: 2 },
                        { label: 'Cohort Q2-2025 (Leo dốc)', data: data.vintage.datasets[1].data, borderColor: '#ef4444', tension: 0.3, borderWidth: 4, pointRadius: 5 },
                        { 
                            label: 'Ngưỡng an toàn (3%)', 
                            data: [3, 3, 3, 3, 3, 3], 
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
                        tooltip: { callbacks: { label: c => c.dataset.label + ': ' + c.parsed.y + '%' } },
                        legend: { labels: { color: '#94a3b8', font: { size: 10 }, boxWidth: 12 } }
                    },
                    scales: { 
                        y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { callback: v => v + '%', color: '#94a3b8' } },
                        x: { grid: { display: false }, ticks: { color: '#94a3b8' } }
                    }
                }
            });
        }

        // 3. Roll Rate Matrix Heatmap Table
        const rollRateContainer = document.getElementById('rollRateContainer');
        if (rollRateContainer && data.roll_matrix) {
            let rowsHtml = '';
            data.roll_matrix.forEach(row => {
                const getHeatBg = val => {
                    if (val > 80) return 'rgba(0,166,81,0.7)';
                    if (val > 50) return 'rgba(0,166,81,0.5)';
                    if (val > 25) return 'rgba(239,68,68,0.5)';
                    if (val > 10) return 'rgba(245,158,11,0.3)';
                    if (val > 5) return 'rgba(245,158,11,0.15)';
                    return 'transparent';
                };
                rowsHtml += `
                    <tr style="height: auto;">
                        <td style="color: var(--text-muted); font-weight: bold; text-align: left; padding: 6px 0;">${row.from}</td>
                        <td style="background: ${getHeatBg(row.to_m0)}; border-radius: 4px; color: white;">${row.to_m0}%</td>
                        <td style="background: ${getHeatBg(row.to_m1)}; border-radius: 4px;">${row.to_m1}%</td>
                        <td style="background: ${getHeatBg(row.to_m2)}; border-radius: 4px;">${row.to_m2}%</td>
                        <td style="background: ${getHeatBg(row.to_m3)}; border-radius: 4px; ${row.to_m3 > 20 ? 'border: 2px solid var(--danger); font-weight: 800; color: #fff;' : ''}">${row.to_m3}%</td>
                    </tr>
                `;
            });
            rollRateContainer.innerHTML = `
                <div style="margin-bottom: 8px; font-size: 10px; color: var(--text-muted); font-style: italic;">
                    * Cách đọc: Một khách hàng ở nhóm "Từ" (hàng) có bao nhiêu % xác suất chuyển sang nhóm "Đến" (cột) trong kỳ tiếp theo.
                </div>
                <table style="width: 100%; height: calc(100% - 25px); border-collapse: separate; border-spacing: 4px; font-size: 11px; table-layout: fixed;">
                    <thead>
                        <tr style="color: var(--text-muted); height: 30px;">
                            <th style="width: 24%; text-align: left;">Từ \\ Đến</th>
                            <th style="text-align: center;">M0 (Trong hạn)</th>
                            <th style="text-align: center;">M1 (1-14d)</th>
                            <th style="text-align: center;">M2 (15-30d)</th>
                            <th style="text-align: center;">M3+ (30d+)</th>
                        </tr>
                    </thead>
                    <tbody style="font-weight: 500; text-align: center;">
                        ${rowsHtml}
                    </tbody>
                </table>
            `;
        }

        // 4. Overdue by district (Horizontal Bar Chart)
        const ctxDistrict = document.getElementById('riskHBarChart');
        if (ctxDistrict && data.districts) {
            window.riskCharts.district = new Chart(ctxDistrict.getContext('2d'), {
                type: 'bar',
                data: { 
                    labels: data.districts.labels, 
                    datasets: [
                        { 
                            label: 'Tỷ lệ Quá hạn %', 
                            data: data.districts.values, 
                            backgroundColor: function(context) {
                                const value = context.dataset.data[context.dataIndex];
                                return value > 6 ? '#ef4444' : value > 4 ? '#f59e0b' : '#00a651';
                            },
                            borderRadius: 4,
                            barThickness: 20
                        },
                        {
                            label: 'Trung bình (5.2%)',
                            data: Array(data.districts.values.length).fill(5.2),
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
                    scales: { 
                        x: { ticks: { callback: v => v + '%', color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                        y: { ticks: { color: '#94a3b8' } }
                    } 
                }
            });
        }

        // 5. Cấu trúc Từ chối (Pie Chart)
        const ctxType = document.getElementById('riskTypePie');
        if (ctxType && data.rejections) {
            window.riskCharts.type = new Chart(ctxType.getContext('2d'), {
                type: 'pie',
                data: { 
                    labels: data.rejection_labels, 
                    datasets: [{ 
                        data: data.rejections, 
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
                                    const d = chart.data;
                                    return d.labels.map((label, i) => {
                                        const value = d.datasets[0].data[i];
                                        const total = d.datasets[0].data.reduce((a, b) => a + b, 0);
                                        const percentage = ((value / total) * 100).toFixed(0) + '%';
                                        return {
                                            text: `${label}: ${percentage} (${value} hồ sơ)`,
                                            fillStyle: d.datasets[0].backgroundColor[i],
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
        }

        // 6. Phân tán LTV vs Thu Nhập (Bubble Chart)
        const ctxBubble = document.getElementById('riskBubbleChart');
        if (ctxBubble && data.bubble) {
            window.riskCharts.bubble = new Chart(ctxBubble.getContext('2d'), {
                type: 'bubble',
                data: {
                    datasets: [
                        {
                            label: 'Rủi ro thấp (Trong hạn)',
                            data: data.bubble.low,
                            backgroundColor: 'rgba(0, 166, 81, 0.6)',
                            borderColor: '#fff',
                            borderWidth: 1
                        },
                        {
                            label: 'Rủi ro trung bình (M1)',
                            data: data.bubble.med,
                            backgroundColor: 'rgba(245, 158, 11, 0.6)',
                            borderColor: '#fff',
                            borderWidth: 1
                        },
                        {
                            label: 'Rủi ro cao (M2+)',
                            data: data.bubble.high,
                            backgroundColor: 'rgba(239, 68, 68, 0.6)',
                            borderColor: '#fff',
                            borderWidth: 1
                        }
                    ]
                },
                options: { 
                    plugins: { 
                        legend: { position: 'bottom', labels: { color: '#94a3b8', font: { size: 9 }, boxWidth: 10 } }, 
                        tooltip: { 
                            callbacks: { 
                                label: function(context) { 
                                    const raw = context.raw;
                                    return [
                                        `Thu nhập: ${raw.x}M VNĐ`,
                                        `LTV: ${raw.y}%`,
                                        `Quy mô Vay: ${raw.r * 10}tr`
                                    ];
                                } 
                            } 
                        } 
                    },
                    scales: { 
                        x: { 
                            title: { display: true, text: 'Thu nhập hàng tháng (M)', color: '#94a3b8', font: { size: 10 } },
                            ticks: { callback: v => v + 'M', color: '#94a3b8' },
                            grid: { color: 'rgba(255,255,255,0.05)' }
                        }, 
                        y: { 
                            title: { display: true, text: 'Tỷ lệ LTV (%)', color: '#94a3b8', font: { size: 10 } },
                            ticks: { callback: v => v + '%', color: '#94a3b8' },
                            grid: { color: 'rgba(255,255,255,0.05)' }
                        } 
                    }
                }
            });
        }

    } catch (err) {
        console.error('Lỗi khi tải dữ liệu Risk tab:', err);
    }
}
