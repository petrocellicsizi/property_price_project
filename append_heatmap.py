# -*- coding: utf-8 -*-
import codecs
with codecs.open('static/js/app.js', 'r', 'utf-8') as f:
    content = f.read()

append_code = """
    // --- 11. Heatmap Tab ---
    const btnUpdateHeatmap = document.getElementById('btnUpdateHeatmap');
    const rngHeatmapYear = document.getElementById('rngHeatmapYear');
    const badgeHeatmapYear = document.getElementById('badgeHeatmapYear');
    const heatmapMapContainer = document.getElementById('heatmapMapContainer');
    const tabBtnHeatmap = document.getElementById('tab-btn-heatmap');

    async function fetchAndRenderHeatmap() {
        const startYear = rngHeatmapYear ? rngHeatmapYear.value : 2004;
        const districtElem = document.getElementById('heatmap_district');
        const cityElem = document.getElementById('heatmap_city');
        const district = districtElem ? districtElem.value : 'VIII. kerület';
        const city = cityElem ? cityElem.value : 'Budapest';
        
        if (heatmapMapContainer) {
            heatmapMapContainer.innerHTML = '<div class=\"d-flex h-100 align-items-center justify-content-center text-muted\"><div class=\"spinner-border text-primary me-2\" role=\"status\"></div> Térkép generálása folyamatban...</div>';
        }
        
        try {
            const response = await fetch('/api/heatmap_svg?start_year=' + startYear + '&district=' + encodeURIComponent(district) + '&city=' + encodeURIComponent(city));
            if (response.ok) {
                const svgContent = await response.text();
                if (heatmapMapContainer) {
                    heatmapMapContainer.innerHTML = svgContent;
                }
                const badgeRes = document.getElementById('badgeHeatmapResult');
                if (badgeRes) {
                    badgeRes.textContent = startYear + ' - Napjainkig';
                }
            } else {
                if (heatmapMapContainer) {
                    heatmapMapContainer.innerHTML = '<div class=\"d-flex h-100 align-items-center justify-content-center text-danger\"><i class=\"bi bi-exclamation-triangle-fill me-2\"></i> Hiba történt a generálás során.</div>';
                }
            }
        } catch (e) {
            console.error('Hiba a heatmap hívásakor:', e);
            if (heatmapMapContainer) {
                heatmapMapContainer.innerHTML = '<div class=\"d-flex h-100 align-items-center justify-content-center text-danger\"><i class=\"bi bi-exclamation-triangle-fill me-2\"></i> Hiba történt a generálás során.</div>';
            }
        }
    }

    if (rngHeatmapYear && badgeHeatmapYear) {
        rngHeatmapYear.addEventListener('input', (e) => {
            badgeHeatmapYear.textContent = e.target.value;
        });
        rngHeatmapYear.addEventListener('change', fetchAndRenderHeatmap);
    }
    
    if (btnUpdateHeatmap) {
        btnUpdateHeatmap.addEventListener('click', (e) => {
            e.preventDefault();
            fetchAndRenderHeatmap();
        });
    }

    if (tabBtnHeatmap) {
        tabBtnHeatmap.addEventListener('shown.bs.tab', () => {
            fetchAndRenderHeatmap();
        });
    }
"""

parts = content.rsplit('});', 1)
new_content = parts[0] + append_code + '\n});'

with codecs.open('static/js/app.js', 'w', 'utf-8') as f:
    f.write(new_content)
