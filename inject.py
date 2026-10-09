with open('static/js/app.js', 'r', encoding='utf-8') as f:
    js = f.read()

sim_chart_code = """
        // 6. Delta Cashflow Chart
        if (ctxDeltaCashflow) {
            const deltaData = traj.monthly_buy_outflow.map((buyCost, idx) => buyCost - traj.monthly_rent_outflow[idx]);
            const pointColors = deltaData.map(v => v > 0 ? 'rgba(220, 53, 69, 0.7)' : 'rgba(25, 135, 84, 0.7)');
            
            deltaCashflowChartInstance = new Chart(ctxDeltaCashflow, {
                type: 'bar',
                data: {
                    labels: traj.year,
                    datasets: [{
                        label: 'Kiadáskülönbség (Vásárlás - Bérlés)',
                        data: deltaData,
                        backgroundColor: pointColors,
                        borderWidth: 0
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: { duration: 0 },
                    plugins: {
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    let val = context.raw;
                                    let prefix = val > 0 ? "Vásárlás drágább: +" : "Bérlés drágább: ";
                                    return prefix + Math.abs(val).toLocaleString('hu-HU') + " Ft/hó";
                                }
                            }
                        }
                    }
                }
            });
        }
"""

hist_chart_code = """
            if (histDeltaCashflowChartInstance) histDeltaCashflowChartInstance.destroy();
            if (ctxHistDeltaCashflow) {
                const histDeltaData = data.buy_cashflows.map((buyCost, idx) => buyCost - data.rent_cashflows[idx]);
                const histPointColors = histDeltaData.map(v => v > 0 ? 'rgba(220, 53, 69, 0.7)' : 'rgba(25, 135, 84, 0.7)');
                
                histDeltaCashflowChartInstance = new Chart(ctxHistDeltaCashflow, {
                    type: 'bar',
                    data: {
                        labels: data.timeline,
                        datasets: [{
                            label: 'Kiadáskülönbség (Vásárlás - Bérlés)',
                            data: histDeltaData,
                            backgroundColor: histPointColors,
                            borderWidth: 0
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            tooltip: {
                                callbacks: {
                                    label: function(context) {
                                        let val = context.raw;
                                        let prefix = val > 0 ? "Vásárlás drágább: +" : "Bérlés drágább: ";
                                        return prefix + Math.abs(val).toLocaleString('hu-HU') + " Ft/hó";
                                    }
                                }
                            }
                        }
                    }
                });
            }
"""

# Insert sim chart right before `function populateForm(data)`
js = js.replace('    function populateForm(data) {', sim_chart_code + '\n    function populateForm(data) {')

# Insert hist chart right before `function applyAiAdjustedSuggestionsToUI(suggestions) {`
js = js.replace('    function applyAiAdjustedSuggestionsToUI(suggestions) {', hist_chart_code + '\n    function applyAiAdjustedSuggestionsToUI(suggestions) {')

with open('static/js/app.js', 'w', encoding='utf-8') as f:
    f.write(js)
