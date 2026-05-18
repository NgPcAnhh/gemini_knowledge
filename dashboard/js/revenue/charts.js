// js/revenue/charts.js

async function initRevenueCharts() {
    const API_BASE = window.F88_API_BASE || `${window.location.protocol}//${window.location.hostname}:8000`;

    // Clean up previous revenue charts to avoid canvas reuse errors
    if (window.revenueCharts) {
        Object.values(window.revenueCharts).forEach(chart => {
            if (chart && typeof chart.destroy === 'function') chart.destroy();
        });
    }
    window.revenueCharts = {};

    try {
        const res = await fetch(`${API_BASE}/api/dashboard/revenue`, { cache: 'no-store' });
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        const data = await res.json();

        // 1. Update Top KPI Cards
        if (data.kpis) {
            const kpis = data.kpis;
            const setText = (id, value) => {
                const el = document.getElementById(id);
                if (el) el.textContent = value;
            };
            setText('val-rev-cap-util', `${kpis.cap_util_rate}%`);
            setText('val-rev-disb', `${kpis.disb_rate}%`);
            setText('val-rev-coll', `${kpis.coll_rate}%`);
            setText('val-rev-roi', `${kpis.roi}%`);
            setText('val-rev-net-yield', `${kpis.net_yield}%`);
            setText('val-rev-per-loan', `${kpis.rev_per_loan}K`);
        }

        // 2. Ticket Size Distribution (Doughnut)
        const ctxTicket = document.getElementById('ticketSizeDistribution');
        if (ctxTicket && data.ticket_size) {
            window.revenueCharts.ticket = new Chart(ctxTicket.getContext('2d'), {
                type: 'doughnut',
                data: {
                    labels: ['Nhỏ (<10tr)', 'Vừa (10-50tr)', 'Lớn (>50tr)'],
                    datasets: [{
                        data: data.ticket_size,
                        backgroundColor: ['#00a651', '#f59e0b', '#ef4444'],
                        borderWidth: 0
                    }]
                },
                options: {
                    cutout: '60%',
                    layout: { padding: { top: 10, left: 10, right: 10, bottom: 10 } },
                    plugins: {
                        legend: { position: 'bottom', labels: { font: { size: 10 }, color: '#ffffff', boxWidth: 10 } }
                    }
                }
            });
        }

        // 3. Average Loan Size & Disbursement Combo (Bar + Line)
        const ctxCombo = document.getElementById('avgLoanSizeCombo');
        if (ctxCombo && data.trend) {
            window.revenueCharts.combo = new Chart(ctxCombo.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: data.trend.months,
                    datasets: [
                        {
                            type: 'line',
                            label: 'Quy mô TB (ngàn)',
                            data: data.trend.avg_sizes,
                            borderColor: '#00a651',
                            yAxisID: 'y1',
                            tension: 0.4,
                            pointRadius: 4,
                            pointBackgroundColor: '#00a651'
                        },
                        {
                            type: 'bar',
                            label: 'Giải ngân (triệu)',
                            data: data.trend.disbursements,
                            backgroundColor: '#ffc20e',
                            borderRadius: 4,
                            yAxisID: 'y'
                        }
                    ]
                },
                options: {
                    scales: {
                        y: { position: 'left', grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { callback: v => v + 'M', color: '#94a3b8' } },
                        y1: { position: 'right', grid: { drawOnChartArea: false }, ticks: { callback: v => v + 'K', color: '#94a3b8' } },
                        x: { grid: { display: false }, ticks: { color: '#94a3b8' } }
                    },
                    plugins: { 
                        legend: { position: 'top', labels: { color: '#94a3b8', font: { size: 10 } } },
                        tooltip: { callbacks: { label: c => c.dataset.label + ': ' + c.parsed.y } }
                    }
                }
            });
        }

        // 4. Cost of Fund vs Yield on Portfolio (Line Chart)
        const ctxCY = document.getElementById('costYieldComparison');
        if (ctxCY && data.cost_yield) {
            window.revenueCharts.costYield = new Chart(ctxCY.getContext('2d'), {
                type: 'line',
                data: {
                    labels: data.cost_yield.months,
                    datasets: [
                        { 
                            label: 'Lợi suất danh nghĩa (%)', 
                            data: data.cost_yield.yields, 
                            borderColor: '#00a651', 
                            backgroundColor: 'rgba(0, 166, 81, 0.1)', 
                            fill: true, 
                            tension: 0.3 
                        },
                        { 
                            label: 'Tỷ lệ Chi phí vận hành (%)', 
                            data: data.cost_yield.costs, 
                            borderColor: '#f59e0b', 
                            backgroundColor: 'rgba(245, 158, 11, 0.1)', 
                            fill: true, 
                            tension: 0.3 
                        }
                    ]
                },
                options: {
                    scales: { 
                        y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { callback: v => v + '%', color: '#94a3b8' } },
                        x: { grid: { display: false }, ticks: { color: '#94a3b8' } }
                    },
                    plugins: { 
                        legend: { position: 'top', labels: { color: '#94a3b8', font: { size: 10 } } },
                        tooltip: { callbacks: { label: c => c.dataset.label + ': ' + c.parsed.y + '%' } } 
                    }
                }
            });
        }

        // 5. Net Revenue per Loan (Bar Chart)
        const ctxNR = document.getElementById('netRevenuePerLoan');
        if (ctxNR && data.net_revenue) {
            window.revenueCharts.netRev = new Chart(ctxNR.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: data.net_revenue.months,
                    datasets: [{
                        label: 'Doanh thu / HĐ (ngàn)',
                        data: data.net_revenue.values,
                        backgroundColor: '#3b82f6',
                        borderRadius: 4,
                        borderWidth: 0
                    }]
                },
                options: {
                    plugins: { legend: { display: false }, tooltip: { callbacks: { label: c => c.parsed.y + 'K VND' } } },
                    scales: { 
                        y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { callback: v => v + 'K', color: '#94a3b8' } },
                        x: { grid: { display: false }, ticks: { color: '#94a3b8' } }
                    }
                }
            });
        }

        // 6. Loan Growth Rate Timeline (Line Chart)
        const ctxGrowth = document.getElementById('loanGrowthTimeline');
        if (ctxGrowth && data.trend && data.trend.growth_rates) {
            window.revenueCharts.growth = new Chart(ctxGrowth.getContext('2d'), {
                type: 'line',
                data: {
                    labels: data.trend.months,
                    datasets: [{
                        label: 'Tốc độ Tăng trưởng (%)',
                        data: data.trend.growth_rates,
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
                                title: c => 'Tháng: ' + c[0].label,
                                label: c => 'Tăng trưởng: ' + c.parsed.y + '% (YoY)'
                            }
                        }
                    },
                    scales: { 
                        y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { callback: v => v + '%', color: '#94a3b8' } },
                        x: { grid: { display: false }, ticks: { color: '#94a3b8' } }
                    }
                }
            });
        }

        // 7. Outstanding Loan Distribution (Pie Chart)
        const ctxOut = document.getElementById('outstandingLoanPie');
        if (ctxOut && data.outstanding_pie) {
            window.revenueCharts.outstanding = new Chart(ctxOut.getContext('2d'), {
                type: 'pie',
                data: {
                    labels: data.outstanding_labels || ['Hoạt động', 'Quá hạn', 'Đã tất toán'],
                    datasets: [{
                        data: data.outstanding_pie,
                        backgroundColor: ['#00a651', '#ffc20e', '#6b7280'],
                        borderWidth: 0
                    }]
                },
                options: {
                    plugins: { 
                        legend: { position: 'bottom', labels: { font: { size: 9 }, color: '#94a3b8' } } 
                    }
                }
            });
        }

    } catch (err) {
        console.error('Lỗi khi tải dữ liệu Revenue tab:', err);
    }
}

function roundTo(value, decimals) {
    return Number(Math.round(value + 'e' + decimals) + 'e-' + decimals);
}
