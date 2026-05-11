// js/realtime/map.js

function initVietnamMap() {
    const vnBounds = L.latLngBounds([8.5, 102.0], [23.5, 109.5]);
    const map = L.map('vnMap', {
        zoomControl: true,
        attributionControl: false,
        minZoom: 5,
        maxZoom: 10
    });
    map.fitBounds(vnBounds);
    window._vnMap = map;
    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}{r}.png').addTo(map);

    // Mock province risk data
    const provinceRisk = {
        'Ho Chi Minh': { risk: 'high', weather: 'Mưa lớn, Kẹt xe', loans: '1,830', impact: '-22%', temp: '28°C' },
        'Ha Noi': { risk: 'low', weather: 'Nắng ráo', loans: '1,050', impact: '+2%', temp: '32°C' },
        'Da Nang': { risk: 'medium', weather: 'Mưa rải rác', loans: '420', impact: '-5%', temp: '30°C' },
        'Can Tho': { risk: 'low', weather: 'Ổn định', loans: '310', impact: '0%', temp: '31°C' },
        'Binh Duong': { risk: 'medium', weather: 'Mưa nhẹ', loans: '280', impact: '-8%', temp: '29°C' },
        'Dong Nai': { risk: 'medium', weather: 'Mưa nhẹ', loans: '190', impact: '-6%', temp: '29°C' },
        'Hai Phong': { risk: 'low', weather: 'Nắng', loans: '150', impact: '+1%', temp: '31°C' },
        'Khanh Hoa': { risk: 'low', weather: 'Nắng', loans: '90', impact: '0%', temp: '33°C' },
    };

    function getRiskColor(risk) {
        if (risk === 'high') return '#ef4444';
        if (risk === 'medium') return '#ffc20e';
        return '#00a651';
    }

    // City markers with tooltips
    const cities = [
        { name: 'Hà Nội', key: 'Ha Noi', lat: 21.028, lng: 105.854 },
        { name: 'TP. Hồ Chí Minh', key: 'Ho Chi Minh', lat: 10.823, lng: 106.630 },
        { name: 'Đà Nẵng', key: 'Da Nang', lat: 16.054, lng: 108.202 },
        { name: 'Cần Thơ', key: 'Can Tho', lat: 10.045, lng: 105.746 },
        { name: 'Bình Dương', key: 'Binh Duong', lat: 11.166, lng: 106.629 },
        { name: 'Đồng Nai', key: 'Dong Nai', lat: 10.945, lng: 106.824 },
        { name: 'Hải Phòng', key: 'Hai Phong', lat: 20.844, lng: 106.688 },
        { name: 'Khánh Hòa', key: 'Khanh Hoa', lat: 12.238, lng: 109.196 },
    ];

    cities.forEach(c => {
        const d = provinceRisk[c.key] || { risk: 'low', weather: 'N/A', loans: '0', impact: '0%', temp: 'N/A' };
        const color = getRiskColor(d.risk);
        const marker = L.circleMarker([c.lat, c.lng], { radius: 7, fillColor: color, color: color, weight: 2, opacity: 0.9, fillOpacity: 0.6 }).addTo(map);
        marker.bindTooltip(
            `<b>${c.name}</b><br>` +
            `<span style='color:#94a3b8'>Thời tiết:</span> ${d.weather} (${d.temp})<br>` +
            `<span style='color:#94a3b8'>Active HĐ:</span> ${d.loans}<br>` +
            `<span style='color:#94a3b8'>Ước tính thu:</span> <span style='color:${color}'>${d.impact}</span>`,
            { className: 'leaflet-tooltip-custom', direction: 'right', offset: [10, 0] }
        );
    });

    // Load GeoJSON provinces
    fetch('https://raw.githubusercontent.com/TungTh/tungth.github.io/master/data/vietnam.geojson')
        .then(r => r.json())
        .then(data => {
            L.geoJSON(data, {
                style: function(feature) {
                    const name = feature.properties.Ten_Tinh || feature.properties.name || '';
                    let matchedRisk = 'low';
                    for (const [key, val] of Object.entries(provinceRisk)) {
                        if (name.toLowerCase().includes(key.toLowerCase().split(' ')[0])) { matchedRisk = val.risk; break; }
                    }
                    return { 
                        color: '#00a651', // In đậm màu xanh lá cho ranh giới
                        weight: 2, 
                        opacity: 0.8,
                        fillColor: getRiskColor(matchedRisk), 
                        fillOpacity: matchedRisk === 'low' ? 0.05 : 0.25 
                    };
                },
                onEachFeature: function(feature, layer) {
                    const name = feature.properties.Ten_Tinh || feature.properties.name || 'N/A';
                    layer.bindTooltip(name, { className: 'leaflet-tooltip-custom', sticky: true });
                    layer.on('mouseover', function() { this.setStyle({ fillOpacity: 0.4, weight: 3, opacity: 1 }); });
                    layer.on('mouseout', function() { 
                        let matchedRisk = 'low';
                        for (const [key, val] of Object.entries(provinceRisk)) {
                            if (name.toLowerCase().includes(key.toLowerCase().split(' ')[0])) { matchedRisk = val.risk; break; }
                        }
                        this.setStyle({ fillOpacity: matchedRisk === 'low' ? 0.05 : 0.25, weight: 2, opacity: 0.8 }); 
                    });
                }
            }).addTo(map);
        })
        .catch(() => { console.warn('GeoJSON load failed, map shows markers only.'); });

    setTimeout(() => map.invalidateSize(), 300);
}
