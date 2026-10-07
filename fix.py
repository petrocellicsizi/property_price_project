with open('templates/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()
new_lines = lines[:534] + [
    '                                </div>\n',
    '                            </div>\n',
    '                        </div>\n',
    '                    </div>\n',
    '                </div>\n',
    '            </div>\n',
    '        </div>\n',
    '        <div class="row mt-4 mb-2 justify-content-center">\n',
    '            <div class="col-lg-6">\n',
    '                <div class="d-grid">\n',
    '                    <button type="button" class="btn btn-primary btn-lg fw-bold shadow" id="btnRunSimulation">\n',
    '                        <i class="bi bi-play-fill me-1 fs-5"></i> Szimuláció Futtatása & Eredmények Megtekintése <i class="bi bi-arrow-right ms-1"></i>\n',
    '                    </button>\n',
    '                </div>\n',
    '            </div>\n',
    '        </div>\n'
]
new_lines += lines[549:]
with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
