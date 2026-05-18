// js/customer/charts.js

async function initCustomerCharts() {
    const API_BASE = window.F88_API_BASE || `${window.location.protocol}//${window.location.hostname}:8000`;
    
    // Clean up previous customer charts to avoid Chart.js canvas reuse errors
    if (window.customerCharts) {
        Object.values(window.customerCharts).forEach(chart => {
            if (chart && typeof chart.destroy === 'function') chart.destroy();
        });
    }
    window.customerCharts = {};

    try {
        const res = await fetch(`${API_BASE}/api/dashboard/customer`, { cache: 'no-store' });
        if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
        const data = await res.json();

        // 1. Update radiating mind map KPI nodes
        if (data.kpis) {
            const kpis = data.kpis;
            const setText = (id, value) => {
                const el = document.getElementById(id);
                if (el) el.textContent = value;
            };
            
            setText('val-cust-active', Number(kpis.active_cnt || 0).toLocaleString());
            setText('val-cust-reborrow', `${kpis.reborrow_rate}%`);
            setText('val-cust-credit-score', kpis.avg_score);
            setText('val-cust-avg-age', kpis.avg_age);
            setText('val-cust-avg-term', `${kpis.avg_term}th`);
            setText('val-cust-avg-dti', `${kpis.avg_dti}%`);
            setText('val-cust-avg-income', `${kpis.avg_income}M`);
            setText('val-cust-churn', `${kpis.churn_rate}%`);

            // Update insights
            const insightAge = document.getElementById('val-cust-insight-age');
            const insightDti = document.getElementById('val-cust-insight-dti');
            const insightReborrow = document.getElementById('val-cust-insight-reborrow');
            
            if (insightAge) {
                insightAge.innerHTML = `<i class="fa-solid fa-circle-check" style="color: var(--f88-green);"></i> Nam giới, ~${kpis.avg_age}t.`;
            }
            if (insightDti) {
                const isHighRisk = kpis.avg_dti > 45;
                insightDti.innerHTML = `<i class="fa-solid fa-triangle-exclamation" style="color: ${isHighRisk ? 'var(--danger)' : 'var(--f88-yellow)'};"></i> DTI ${kpis.avg_dti}% (${isHighRisk ? 'Rủi ro' : 'An toàn'}).`;
            }
            if (insightReborrow) {
                insightReborrow.innerHTML = `<i class="fa-solid fa-rotate" style="color: var(--f88-yellow);"></i> Tái vay ${kpis.reborrow_rate}%.`;
            }
        }

        // 2. Phân bổ Thu nhập theo Nhóm Rủi ro (Stacked Bar)
        const ctxStacked = document.getElementById('incomeRiskStackedBar');
        if (ctxStacked && data.stacked) {
            window.customerCharts.stacked = new Chart(ctxStacked.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: data.stacked.labels,
                    datasets: [
                        { label: 'Rủi ro thấp', data: data.stacked.low, backgroundColor: '#00a651' },
                        { label: 'Rủi ro trung bình', data: data.stacked.med, backgroundColor: '#f59e0b' },
                        { label: 'Rủi ro cao', data: data.stacked.high, backgroundColor: '#ef4444' }
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
        }

        // 3. Tuổi vs Thu nhập (Bubble Chart)
        const ctxBubble = document.getElementById('ageIncomeBubblePAR');
        if (ctxBubble && data.bubble) {
            window.customerCharts.bubble = new Chart(ctxBubble.getContext('2d'), {
                type: 'bubble',
                data: {
                    datasets: [
                        { 
                            label: 'PAR < 5%', 
                            data: data.bubble.low, 
                            backgroundColor: 'rgba(0, 166, 81, 0.6)', borderColor: '#fff' 
                        },
                        { 
                            label: 'PAR 5-15%', 
                            data: data.bubble.med, 
                            backgroundColor: 'rgba(245, 158, 11, 0.6)', borderColor: '#fff' 
                        },
                        { 
                            label: 'PAR > 15%', 
                            data: data.bubble.high, 
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
        }

        // 4. Nghề nghiệp vs PAR Rate (Horizontal Bar)
        const ctxJob = document.getElementById('jobPARHBar');
        if (ctxJob && data.jobs) {
            window.customerCharts.job = new Chart(ctxJob.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: data.jobs.labels,
                    datasets: [{
                        label: 'Tỷ lệ PAR 30+ (%)',
                        data: data.jobs.values,
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
        }

        // 5. Phân bổ Credit Score (Histogram)
        const ctxScore = document.getElementById('creditScoreHistogram');
        if (ctxScore && data.histogram) {
            window.customerCharts.score = new Chart(ctxScore.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: ['300-400', '400-500', '500-600', '600-700', '700-800', '800-850'],
                    datasets: [{
                        label: 'Số lượng KH',
                        data: data.histogram,
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

    } catch (err) {
        console.error('Lỗi khi tải dữ liệu Customer tab:', err);
    }
}
