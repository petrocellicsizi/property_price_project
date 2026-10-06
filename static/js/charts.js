/**
 * Plotly.js alapú interaktív vizualizációs modul
 * Nettó vagyongörbék, havi cash-flow terhelés és érzékenységi hőtérkép.
 */

const ChartsModule = {
    /**
     * Nettó vagyongörbék (Net Worth) és BEP metszéspont renderelése
     */
    renderWealthTrajectories: function(trajectories, summary) {
        const years = trajectories.year;
        const buyNW = trajectories.buy_net_worth.map(v => v / 1_000_000);
        const rentNW = trajectories.rent_net_worth.map(v => v / 1_000_000);
        const propVal = trajectories.property_market_value.map(v => v / 1_000_000);
        const loanBal = trajectories.remaining_loan_balance.map(v => v / 1_000_000);

        const traceBuy = {
            x: years,
            y: buyNW,
            mode: 'lines',
            name: 'Saját lakás (Nettó vagyon)',
            line: { color: '#0d6efd', width: 3.5 }
        };

        const traceRent = {
            x: years,
            y: rentNW,
            mode: 'lines',
            name: 'Bérlés + Tőkepiaci portfólió',
            line: { color: '#fd7e14', width: 3, dash: 'dash' }
        };

        const traceProperty = {
            x: years,
            y: propVal,
            mode: 'lines',
            name: 'Ingatlan piaci értéke',
            line: { color: '#6c757d', width: 1.5, dash: 'dot' },
            visible: 'legendonly'
        };

        const traceLoan = {
            x: years,
            y: loanBal,
            mode: 'lines',
            name: 'Fennmaradó hiteltartozás',
            line: { color: '#dc3545', width: 1.5, dash: 'dot' },
            visible: 'legendonly'
        };

        const annotations = [];
        if (summary.break_even_year !== null && summary.break_even_month !== null) {
            const bepIdx = Math.min(summary.break_even_month - 1, buyNW.length - 1);
            annotations.push({
                x: summary.break_even_year,
                y: buyNW[bepIdx],
                xref: 'x',
                yref: 'y',
                text: `<b>Break-Even Pont:</b><br>${summary.break_even_year} év (${summary.break_even_month}. hó)`,
                showarrow: true,
                arrowhead: 2,
                arrowsize: 1.2,
                arrowwidth: 2,
                arrowcolor: '#198754',
                ax: -50,
                ay: -60,
                font: { size: 12, color: '#ffffff' },
                bgcolor: '#198754',
                bordercolor: '#146c43',
                borderwidth: 1,
                borderpad: 6
            });
        }

        const layout = {
            title: {
                text: '<b>Kumulált Nettó Vagyon Időbeli Alakulása (30 év)</b>',
                font: { size: 16, color: '#212529' }
            },
            xaxis: {
                title: 'Eltelt idő (Év)',
                dtick: 2,
                showgrid: true,
                gridcolor: '#e9ecef'
            },
            yaxis: {
                title: 'Nettó Vagyon (Millió Ft)',
                tickformat: ',.0f',
                showgrid: true,
                gridcolor: '#e9ecef'
            },
            hovermode: 'x unified',
            annotations: annotations,
            paper_bgcolor: 'transparent',
            plot_bgcolor: '#ffffff',
            margin: { t: 50, r: 20, l: 60, b: 50 },
            legend: {
                orientation: 'h',
                y: -0.2,
                x: 0.1
            }
        };

        const config = { responsive: true, displayModeBar: true, displaylogo: false };
        Plotly.react('chartWealthDiv', [traceBuy, traceRent, traceProperty, traceLoan], layout, config);
    },

    /**
     * Havi Cash Flow terhelés (Kiadások összehasonlítása)
     */
    renderCashflowComparison: function(trajectories) {
        const years = trajectories.year;
        const buyCF = trajectories.monthly_buy_outflow;
        const rentCF = trajectories.monthly_rent_outflow;

        const traceBuyCF = {
            x: years,
            y: buyCF,
            mode: 'lines',
            name: 'Saját lakás havi kiadása (Törlesztő + Rezsialap)',
            line: { color: '#0d6efd', width: 2.5 },
            fill: 'tozeroy',
            fillcolor: 'rgba(13, 110, 253, 0.08)'
        };

        const traceRentCF = {
            x: years,
            y: rentCF,
            mode: 'lines',
            name: 'Bérlés havi díja (Inflációval növelve)',
            line: { color: '#fd7e14', width: 2.5 },
            fill: 'tozeroy',
            fillcolor: 'rgba(253, 126, 20, 0.08)'
        };

        const layout = {
            title: {
                text: '<b>Havi Készpénzkiadások Alakulása (Cash Outflow)</b>',
                font: { size: 16, color: '#212529' }
            },
            xaxis: {
                title: 'Eltelt idő (Év)',
                dtick: 2,
                showgrid: true,
                gridcolor: '#e9ecef'
            },
            yaxis: {
                title: 'Havi Költség (Ft/hó)',
                tickformat: ',.0f',
                showgrid: true,
                gridcolor: '#e9ecef'
            },
            hovermode: 'x unified',
            paper_bgcolor: 'transparent',
            plot_bgcolor: '#ffffff',
            margin: { t: 50, r: 20, l: 70, b: 50 },
            legend: {
                orientation: 'h',
                y: -0.2,
                x: 0.1
            }
        };

        const config = { responsive: true, displayModeBar: true, displaylogo: false };
        Plotly.react('chartCashflowDiv', [traceBuyCF, traceRentCF], layout, config);
    },

    /**
     * Érzékenységi 2D Hőtérkép (Kamatláb vs. Áremelkedés -> BEP év)
     */
    renderSensitivityHeatmap: function(sensitivityData) {
        const xValues = sensitivityData.property_growth_rates_pct.map(v => `${v}% növekedés`);
        const yValues = sensitivityData.interest_rates_pct.map(v => `${v}% hitelkamat`);
        const zValues = sensitivityData.bep_years_matrix;

        const data = [{
            x: xValues,
            y: yValues,
            z: zValues,
            type: 'heatmap',
            colorscale: [
                [0.0, '#198754'],   // Gyors megtérülés (< 5 év - zöld)
                [0.3, '#ffc107'],   // Közepes megtérülés (8-10 év - sárga)
                [0.6, '#fd7e14'],   // Lassú megtérülés (15-20 év - narancs)
                [1.0, '#dc3545']    // Nem / nagyon későn térül meg (30+ év - piros)
            ],
            colorbar: {
                title: 'BEP Években',
                ticksuffix: ' év'
            },
            hoverongaps: false
        }];

        const layout = {
            title: {
                text: '<b>Érzékenységi Mátrix: Break-Even Év (Kamat vs. Felértékelődés)</b>',
                font: { size: 16, color: '#212529' }
            },
            xaxis: { title: 'Éves Ingatlan Felértékelődés' },
            yaxis: { title: 'Éves Hitelkamat (THM)' },
            paper_bgcolor: 'transparent',
            margin: { t: 50, r: 40, l: 90, b: 60 }
        };

        const config = { responsive: true, displayModeBar: true, displaylogo: false };
        Plotly.react('chartHeatmapDiv', data, layout, config);
    }
};
