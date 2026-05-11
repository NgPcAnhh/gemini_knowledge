// js/common/utils.js

// Global Chart Defaults
Chart.defaults.color = '#94a3b8';
Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.05)';
Chart.defaults.font.family = "'Inter', sans-serif";
Chart.defaults.maintainAspectRatio = false;
Chart.defaults.plugins.legend.labels.boxWidth = 10;
Chart.defaults.plugins.legend.labels.font = { size: 10 };

// Custom Plugins
const centerTextPlugin = {
    id: 'centerText',
    beforeDraw: function(chart) {
        if (chart.config.type !== 'doughnut') return;
        const centerOpts = chart.config.options.plugins?.centerText;
        if (!centerOpts) return;
        const { top, bottom, left, right } = chart.chartArea;
        const cx = (left + right) / 2;
        const cy = (top + bottom) / 2;
        const areaH = bottom - top;
        const ctx = chart.ctx;
        ctx.save();
        const mainSize = centerOpts.fontSize || Math.max(10, areaH / 6);
        ctx.font = 'bold ' + mainSize + 'px Inter';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillStyle = '#fff';
        
        if (centerOpts.subText) {
            ctx.fillText(centerOpts.mainText || '', cx, cy + mainSize * 0.2);
            const subSize = Math.max(8, mainSize * 0.5);
            ctx.font = 'normal ' + subSize + 'px Inter';
            ctx.fillStyle = '#94a3b8';
            ctx.fillText(centerOpts.subText, cx, cy - mainSize * 0.6);
        } else {
            ctx.fillText(centerOpts.mainText || '', cx, cy);
        }
        ctx.restore();
    }
};

const quadrantPlugin = {
    id: 'quadrants',
    beforeDraw: function(chart) {
        if (chart.config.type === 'bubble') {
            const {ctx, chartArea: {top, bottom, left, right}, scales: {x, y}} = chart;
            const midX = x.getPixelForValue(500); // threshold income 500k
            const midY = y.getPixelForValue(40); // threshold LTV 40%
            ctx.save();
            ctx.strokeStyle = 'rgba(255, 255, 255, 0.15)';
            ctx.lineWidth = 1;
            ctx.setLineDash([5, 5]);
            
            // Draw crosshairs
            if(midY >= top && midY <= bottom) { ctx.beginPath(); ctx.moveTo(left, midY); ctx.lineTo(right, midY); ctx.stroke(); }
            if(midX >= left && midX <= right) { ctx.beginPath(); ctx.moveTo(midX, top); ctx.lineTo(midX, bottom); ctx.stroke(); }
            
            // Highlight High Risk Zone (Top Left)
            ctx.fillStyle = 'rgba(239, 68, 68, 0.05)';
            ctx.fillRect(left, top, midX - left, midY - top);
            ctx.fillStyle = 'rgba(239, 68, 68, 0.8)';
            ctx.font = "10px Inter";
            ctx.fillText('Rủi ro cao nhất', left + 10, top + 15);
            ctx.restore();
        }
    }
};

Chart.register(centerTextPlugin);
Chart.register(quadrantPlugin);

// Tooltip Formatters
const currencyFormatter = (val) => new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND', maximumSignificantDigits: 3 }).format(val * 1000000);
const percentFormatter = (val) => val + '%';
