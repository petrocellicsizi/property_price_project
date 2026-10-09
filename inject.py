import sys

content = open('templates/index.html', encoding='utf-8').read()

historical_html = """
        <!-- 3. TAB: HISTORICAL -->
        <div class="tab-pane fade" id="tab-historical" role="tabpanel" aria-labelledby="tab-btn-historical">
            <div class="card border-0 shadow-sm mt-4 bg-light">
                <div class="card-body p-3">
                    <div class="row align-items-center">
                        <div class="col-md-4">
                            <label class="form-label fw-bold mb-0"><i class="bi bi-clock-history text-secondary me-2"></i>Induló év (Visszatekintés):</label>
                        </div>
                        <div class="col-md-6">
                            <input type="range" class="form-range" id="rngHistoricalYear" min="2000" max="2024" step="1" value="2004">
                        </div>
                        <div class="col-md-2 text-end">
                            <span class="badge bg-secondary fs-6" id="badgeHistoricalYear">2004</span>
                        </div>
                    </div>
                </div>
            </div>

            <div class="row mt-4 g-4">
                <div class="col-md-4">
                    <div class="card bg-info text-white border-0 shadow-sm h-100">
                        <div class="card-body">
                            <h6 class="text-uppercase fw-bold text-white-50 mb-1 small">Induló tőke (<span class="dyn-start-year">2004</span>)</h6>
                            <h3 class="mb-0 fw-bold" id="valHistInitial">-- Ft</h3>
                            <small class="text-white-50">Jelenlegi lakásárból visszaszámolva</small>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card bg-success text-white border-0 shadow-sm h-100">
                        <div class="card-body">
                            <h6 class="text-uppercase fw-bold text-white-50 mb-1 small">S&P 500 Végérték (Jelenleg)</h6>
                            <h3 class="mb-0 fw-bold" id="valHistSp500">-- Ft</h3>
                            <small class="text-white-50">Évesített hozam: <span id="valHistSpCagr">-- %</span></small>
                        </div>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card bg-primary text-white border-0 shadow-sm h-100">
                        <div class="card-body">
                            <h6 class="text-uppercase fw-bold text-white-50 mb-1 small">Ingatlan Végérték (Jelenleg)</h6>
                            <h3 class="mb-0 fw-bold" id="valHistRe">-- Ft</h3>
                            <small class="text-white-50">Évesített hozam: <span id="valHistReCagr">-- %</span></small>
                        </div>
                    </div>
                </div>
            </div>

            <div class="card border-0 shadow-sm mt-4">
                <div class="card-header bg-white py-3 border-bottom d-flex justify-content-between align-items-center">
                    <div class="d-flex align-items-center gap-2">
                        <i class="bi bi-graph-up text-success fs-5"></i>
                        <h5 class="card-title mb-0 fw-bold">S&P 500 vs. Ingatlan (<span class="dyn-location">Budapest</span>) Múltbeli Alakulása</h5>
                    </div>
                </div>
                <div class="card-body p-3 bg-light">
                    <div class="bg-white p-3 rounded border" style="height: 400px; position: relative;">
                        <canvas id="historicalChart"></canvas>
                    </div>
                </div>
            </div>
        </div> <!-- end of tab-historical -->
"""

new_content = content.replace('        </div> <!-- end of tab-content -->', historical_html + '\n        </div> <!-- end of tab-content -->')
open('templates/index.html', 'w', encoding='utf-8').write(new_content)
print("done")
