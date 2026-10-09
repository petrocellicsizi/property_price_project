import sys

content = open('static/js/app.js', encoding='utf-8').read()

historical_js = """
    // --- 9. Historikus Eredmények Kezelése ---
    const rngHistoricalYear = document.getElementById('rngHistoricalYear');
    const badgeHistoricalYear = document.getElementById('badgeHistoricalYear');
    const valHistInitial = document.getElementById('valHistInitial');
    const valHistSp500 = document.getElementById('valHistSp500');
    const valHistRe = document.getElementById('valHistRe');
    const valHistSpCagr = document.getElementById('valHistSpCagr');
    const valHistReCagr = document.getElementById('valHistReCagr');
    
    let historicalChartInstance = null;

    async function fetchAndRenderHistorical() {
        const startYear = parseInt(rngHistoricalYear.value);
        const city = document.getElementById('prop_city').value || 'Budapest';
        const district = document.getElementById('prop_district').value || 'XI. kerület';
        const currentPrice = parseCleanNumber(document.getElementById('prop_price_total').value);

        try {
            const response = await fetch('/api/historical_simulation', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    start_year: startYear,
                    city: city,
                    district: district,
                    current_property_value_huf: currentPrice
                })
            });

            if (!response.ok) return;
            const res = await response.json();
            if(res.status !== 'success') return;
            
            const data = res.data;
            const kpi = data.kpi;

            // UI Frissítés
            valHistInitial.textContent = formatHUF(data.initial_capital_huf);
            valHistSp500.textContent = formatHUF(kpi.final_sp_value);
            valHistRe.textContent = formatHUF(kpi.final_re_value);
            valHistSpCagr.textContent = kpi.sp_cagr_pct.toFixed(2) + '%';
            valHistReCagr.textContent = kpi.re_cagr_pct.toFixed(2) + '%';

            document.querySelectorAll('.dyn-start-year').forEach(el => el.textContent = startYear);
            document.querySelectorAll('.dyn-location').forEach(el => el.textContent = data.location_used);

            // Chart.js Rajzolás
            const ctx = document.getElementById('historicalChart');
            if(!ctx) return;
            
            if (historicalChartInstance) {
                historicalChartInstance.destroy();
            }

            historicalChartInstance = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.timeline,
                    datasets: [
                        {
                            label: 'S&P 500 Portfólió Értéke (HUF)',
                            data: data.sp500_values,
                            borderColor: '#198754',
                            backgroundColor: 'rgba(25, 135, 84, 0.1)',
                            borderWidth: 2,
                            tension: 0.3,
                            fill: true
                        },
                        {
                            label: 'Ingatlan Értéke (HUF)',
                            data: data.real_estate_values,
                            borderColor: '#0d6efd',
                            backgroundColor: 'rgba(13, 110, 253, 0.1)',
                            borderWidth: 2,
                            tension: 0.3,
                            fill: true
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return context.dataset.label + ': ' + formatHUF(context.raw);
                                }
                            }
                        }
                    },
                    scales: {
                        y: {
                            ticks: {
                                callback: function(value) {
                                    if (value >= 1000000) return (value / 1000000).toFixed(0) + ' MFt';
                                    return formatHUF(value);
                                }
                            }
                        }
                    }
                }
            });

        } catch (err) {
            console.error("Hiba a historikus adatok lekérésekor:", err);
        }
    }

    if (rngHistoricalYear) {
        rngHistoricalYear.addEventListener('input', (e) => {
            badgeHistoricalYear.textContent = e.target.value;
        });
        rngHistoricalYear.addEventListener('change', fetchAndRenderHistorical);
    }
    
    // Frissítés tab váltáskor is, ha a historical tab aktív
    const tabBtnHistorical = document.getElementById('tab-btn-historical');
    if(tabBtnHistorical) {
        tabBtnHistorical.addEventListener('shown.bs.tab', () => {
            fetchAndRenderHistorical();
        });
    }

"""

pos = content.rfind('});')
if pos != -1:
    new_content = content[:pos] + historical_js + '\n' + content[pos:]
    open('static/js/app.js', 'w', encoding='utf-8').write(new_content)
    print("done")
else:
    print("Could not find end of DOMContentLoaded")
