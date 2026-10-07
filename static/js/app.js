/**
 * Bemeneti Dashboard Kliens (Frontend UI Vezérlő)
 * - Architektúra: A teljes pénzügyi és ingatlanpiaci üzleti logika és algoritmus
 *   a Python backendben (utils modulok és /api/calculate végpont) fut!
 * - A JavaScript réteg kizárólag a felhasználói felületért, eseménykezelésért,
 *   a beviteli pontozott számformázásért és a szerverkommunikációért felel.
 */

document.addEventListener('DOMContentLoaded', () => {
    // --- 1. DOM Elemek ---

    // Helyszín és Lakatok (begépelhető input mezők)
    const propCity = document.getElementById('prop_city');
    const propDistrict = document.getElementById('prop_district');
    const btnToggleCityLock = document.getElementById('btnToggleCityLock');
    const btnToggleDistrictLock = document.getElementById('btnToggleDistrictLock');
    const iconLockCity = document.getElementById('iconLockCity');
    const iconLockDistrict = document.getElementById('iconLockDistrict');
    const badgeCityStatus = document.getElementById('badgeCityStatus');
    const badgeDistrictStatus = document.getElementById('badgeDistrictStatus');

    // Ingatlan mezők
    const propType = document.getElementById('prop_type');
    const propCondition = document.getElementById('prop_condition');
    const propSizeSqm = document.getElementById('prop_size_sqm');
    const propRooms = document.getElementById('prop_rooms');
    const propPriceTotal = document.getElementById('prop_price_total');
    const propPriceSqm = document.getElementById('prop_price_sqm');
    const btnResetPrice = document.getElementById('btnResetPrice');
    const badgeSuggestedPriceSqm = document.getElementById('badgeSuggestedPriceSqm');
    const propLawyerPct = document.getElementById('prop_lawyer_pct');
    const propLawyerHuf = document.getElementById('prop_lawyer_huf');
    const propFurnishingHuf = document.getElementById('prop_furnishing_huf');
    const badgeSuggestedFurnishing = document.getElementById('badgeSuggestedFurnishing');
    const btnResetFurnishing = document.getElementById('btnResetFurnishing');

    // Hitel mezők
    const loanDownPaymentPct = document.getElementById('loan_down_payment_pct');
    const loanDownPaymentHuf = document.getElementById('loan_down_payment_huf');
    const rngDownPayment = document.getElementById('rngDownPayment');
    const lblDownPaymentBadge = document.getElementById('lblDownPaymentBadge');
    const loanAmountHuf = document.getElementById('loan_amount_huf');
    const loanTermYears = document.getElementById('loan_term_years');
    const btnTerms = document.querySelectorAll('.btn-term');
    const loanInterestPct = document.getElementById('loan_interest_pct');
    const loanOtherFeesHuf = document.getElementById('loan_other_fees_huf');
    const loanMonthlyPayment = document.getElementById('loan_monthly_payment');
    const lblEstimatedPmt = document.getElementById('lblEstimatedPmt');

    // Bérlés mezők
    const rentMonthlyHuf = document.getElementById('rent_monthly_huf');
    const badgeSuggestedRent = document.getElementById('badgeSuggestedRent');
    const btnResetRent = document.getElementById('btnResetRent');
    const rentUtilitiesHuf = document.getElementById('rent_utilities_huf');
    const badgeSuggestedUtilities = document.getElementById('badgeSuggestedUtilities');
    const btnResetUtilities = document.getElementById('btnResetUtilities');
    const lblTotalRentOutlay = document.getElementById('lblTotalRentOutlay');

    // Befektetés és Makro mezők
    const invReturnPct = document.getElementById('inv_return_pct');
    const rngInvReturn = document.getElementById('rngInvReturn');
    const lblInvReturnBadge = document.getElementById('lblInvReturnBadge');
    const rngPropGrowth = document.getElementById('rngPropGrowth');
    const lblPropGrowthBadge = document.getElementById('lblPropGrowthBadge');
    const rngRentInflation = document.getElementById('rngRentInflation');
    const lblRentInflationBadge = document.getElementById('lblRentInflationBadge');
    const lblMonthlyReturnRate = document.getElementById('lblMonthlyReturnRate');
    const badgeTotalInitialOutlay = document.getElementById('badgeTotalInitialOutlay');

    // Egyéb releváns információk (4 kategória szövegdobozai)
    const propOtherInfo = document.getElementById('prop_other_info');
    const loanOtherInfo = document.getElementById('loan_other_info');
    const rentOtherInfo = document.getElementById('rent_other_info');
    const invOtherInfo = document.getElementById('inv_other_info');

    // Gemini AI Elemzés panel elemei
    const cardGeminiAnalysis = document.getElementById('cardGeminiAnalysis');
    const containerGeminiResults = document.getElementById('containerGeminiResults');
    const badgeGeminiModel = document.getElementById('badgeGeminiModel');

    // Gombok és visszajelzők
    const btnSaveTop = document.getElementById('btnSaveTop');
    const btnResetDefaults = document.getElementById('btnResetDefaults');
    const statusAlert = document.getElementById('statusAlert');
    const statusAlertTitle = document.getElementById('statusAlertTitle');
    const statusAlertMessage = document.getElementById('statusAlertMessage');
    const btnCloseAlert = document.getElementById('btnCloseAlert');

    // Felhasználói egyedi felülírás állapotjelzők
    // Alapértelmezetten true, így induláskor/betöltéskor nem írja felül a mentett értékeket az AI javaslattal.
    // Csak akkor váltanak false-ra, ha a user külön rányom a "Javaslat" gombra.
    let userCustomPrice = true;
    let userCustomFurnishing = true;
    let userCustomRent = true;
    let userCustomUtilities = true;

    // --- 2. Pontozott Formázó Segédfüggvények (UI Gépelési Élményhez) ---

    function formatWithDots(val) {
        if (val === null || val === undefined || val === '') return '';
        const cleanStr = String(val).replace(/\D/g, '');
        if (!cleanStr) return '';
        return cleanStr.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
    }

    function parseCleanNumber(val) {
        if (val === null || val === undefined || val === '') return 0;
        const cleanStr = String(val).replace(/\D/g, '');
        return cleanStr ? parseFloat(cleanStr) : 0;
    }

    function formatHUF(val) {
        if (val === null || val === undefined || isNaN(val) || val === '') return '0 Ft';
        const num = Math.round(Number(val));
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, '.') + ' Ft';
    }

    // Pontozott formázás minden .format-huf mezőre gépeléskor
    const moneyInputs = document.querySelectorAll('.format-huf');
    moneyInputs.forEach(input => {
        input.addEventListener('input', (e) => {
            const rawVal = e.target.value;
            const cursorPos = e.target.selectionStart;
            const prevLen = rawVal.length;

            const formatted = formatWithDots(rawVal);
            e.target.value = formatted;

            const newLen = formatted.length;
            const newCursor = cursorPos + (newLen - prevLen);
            e.target.setSelectionRange(newCursor, newCursor);
        });
    });

    // --- 3. Python Backend Számítási Motor Hívása (/api/calculate) ---

    let calcDebounceTimer = null;
    let currentAiEvaluations = null;

    function triggerPythonCalculations() {
        if (calcDebounceTimer) clearTimeout(calcDebounceTimer);
        calcDebounceTimer = setTimeout(runPythonCalculations, 120);
    }

    async function runPythonCalculations() {
        const payload = collectFormData();
        if (currentAiEvaluations) {
            payload.ai_evaluations = currentAiEvaluations;
        }

        try {
            const response = await fetch('/api/calculate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!response.ok) return;
            const res = await response.json();
            const raw = res.raw;
            const fmt = res.formatted;
            const adjInfo = raw.adjustments_info || {};

            // Python által számított ajánlások frissítése AI jelvénnyel (ha van AI korrekció)
            if (badgeSuggestedPriceSqm) {
                badgeSuggestedPriceSqm.innerHTML = `<i class="bi bi-magic me-1"></i>Javaslat: ${fmt.suggested_price_per_sqm}`;
            }
            if (!userCustomPrice && propPriceSqm && propPriceTotal) {
                propPriceSqm.value = formatWithDots(raw.suggested_price_per_sqm_huf);
                propPriceTotal.value = formatWithDots(raw.suggested_price_total_huf);
                updateLoanFromDownPaymentPct();
            }
            if (badgeSuggestedFurnishing) {
                const furnishAdj = adjInfo.furnishing_adjustment_huf || 0;
                const extraBadge = furnishAdj !== 0 
                    ? ` <span class="badge bg-primary text-white ms-1" style="font-size: 0.7rem;">AI: ${furnishAdj > 0 ? '+' : ''}${formatHUF(furnishAdj)}</span>` 
                    : '';
                badgeSuggestedFurnishing.innerHTML = `<i class="bi bi-magic me-1"></i>Javaslat: ${fmt.suggested_furnishing}${extraBadge}`;
            }
            if (!userCustomFurnishing && propFurnishingHuf) {
                propFurnishingHuf.value = formatWithDots(raw.suggested_furnishing_huf);
            }

            if (badgeSuggestedRent) {
                const rentAdjPct = adjInfo.rent_adjustment_pct || 0;
                const extraBadge = rentAdjPct !== 0 
                    ? ` <span class="badge ${rentAdjPct > 0 ? 'bg-danger' : 'bg-success'} text-white ms-1" style="font-size: 0.7rem;">AI: ${rentAdjPct > 0 ? '+' : ''}${rentAdjPct}%</span>` 
                    : '';
                badgeSuggestedRent.innerHTML = `<i class="bi bi-magic me-1"></i>Javaslat: ${fmt.suggested_rent}${extraBadge}`;
            }
            if (!userCustomRent && rentMonthlyHuf) {
                rentMonthlyHuf.value = formatWithDots(raw.suggested_rent_huf);
            }

            if (badgeSuggestedUtilities) {
                const utilsAdjPct = adjInfo.utilities_adjustment_pct || 0;
                const extraBadge = utilsAdjPct !== 0 
                    ? ` <span class="badge ${utilsAdjPct > 0 ? 'bg-warning text-dark' : 'bg-success text-white'} ms-1" style="font-size: 0.7rem;">AI: ${utilsAdjPct > 0 ? '+' : ''}${utilsAdjPct}%</span>` 
                    : '';
                badgeSuggestedUtilities.innerHTML = `<i class="bi bi-magic me-1"></i>Javaslat: ${fmt.suggested_utilities}${extraBadge}`;
            }
            if (!userCustomUtilities && rentUtilitiesHuf) {
                rentUtilitiesHuf.value = formatWithDots(raw.suggested_utilities_huf);
            }

            // Pénzügyi mutatók frissítése a Python backend válasza alapján
            if (lblEstimatedPmt) {
                lblEstimatedPmt.textContent = fmt.estimated_monthly_payment;
            }
            if (lblTotalRentOutlay) {
                lblTotalRentOutlay.textContent = fmt.total_rent_outlay;
            }
            if (lblMonthlyReturnRate) {
                lblMonthlyReturnRate.textContent = fmt.monthly_return_rate;
            }
            if (badgeTotalInitialOutlay) {
                badgeTotalInitialOutlay.textContent = fmt.total_initial_outlay;
            }

            // --- Új: Kvantitatív Megtérülési Szimuláció (Chart.js) Renderelése ---
            if (raw.simulation) {
                renderWealthChart(raw.simulation);
            }
            if (raw.sensitivity) {
                renderHeatmap(raw.sensitivity);
            }
        } catch (err) {
            console.error("Hiba a Python kvantitatív kalkuláció hívásakor:", err);
        }
    }

    function applyAiAdjustedSuggestionsToUI(adjData) {
        if (!adjData) return;
        const raw = adjData;
        const fmt = adjData.formatted || {};
        const applied = adjData.adjustments_applied || {};

        // 1. Albérlet javaslat AI felülbírálata
        if (badgeSuggestedRent && fmt.suggested_rent) {
            const rentPct = applied.rent_adjustment_pct || 0;
            const badgeExtra = rentPct !== 0 
                ? ` <span class="badge ${rentPct > 0 ? 'bg-danger' : 'bg-success'} text-white ms-1" style="font-size: 0.7rem;">AI: ${rentPct > 0 ? '+' : ''}${rentPct}%</span>` 
                : '';
            badgeSuggestedRent.innerHTML = `<i class="bi bi-magic me-1"></i>Javaslat: ${fmt.suggested_rent}${badgeExtra}`;
        }
        if ((!userCustomRent || (applied.rent_adjustment_pct && applied.rent_adjustment_pct !== 0)) && raw.suggested_rent_huf) {
            rentMonthlyHuf.value = formatWithDots(raw.suggested_rent_huf);
            userCustomRent = false;
        }

        // 2. Rezsi javaslat AI felülbírálata
        if (badgeSuggestedUtilities && fmt.suggested_utilities) {
            const utilsPct = applied.utilities_adjustment_pct || 0;
            const badgeExtra = utilsPct !== 0 
                ? ` <span class="badge ${utilsPct > 0 ? 'bg-warning text-dark' : 'bg-success text-white'} ms-1" style="font-size: 0.7rem;">AI: ${utilsPct > 0 ? '+' : ''}${utilsPct}%</span>` 
                : '';
            badgeSuggestedUtilities.innerHTML = `<i class="bi bi-magic me-1"></i>Javaslat: ${fmt.suggested_utilities}${badgeExtra}`;
        }
        if ((!userCustomUtilities || (applied.utilities_adjustment_pct && applied.utilities_adjustment_pct !== 0)) && raw.suggested_utilities_huf) {
            rentUtilitiesHuf.value = formatWithDots(raw.suggested_utilities_huf);
            userCustomUtilities = false;
        }

        // 3. Bútorozási javaslat AI felülbírálata
        if (badgeSuggestedFurnishing && fmt.suggested_furnishing) {
            const furnishHuf = applied.furnishing_adjustment_huf || 0;
            const badgeExtra = furnishHuf !== 0 
                ? ` <span class="badge ${furnishHuf > 0 ? 'bg-primary' : 'bg-success'} text-white ms-1" style="font-size: 0.7rem;">AI: ${furnishHuf > 0 ? '+' : ''}${formatHUF(furnishHuf)}</span>` 
                : '';
            badgeSuggestedFurnishing.innerHTML = `<i class="bi bi-magic me-1"></i>Javaslat: ${fmt.suggested_furnishing}${badgeExtra}`;
        }
        if ((!userCustomFurnishing || (applied.furnishing_adjustment_huf && applied.furnishing_adjustment_huf !== 0)) && raw.suggested_furnishing_huf) {
            propFurnishingHuf.value = formatWithDots(raw.suggested_furnishing_huf);
            userCustomFurnishing = false;
        }

        runPythonCalculations();
    }

    // Felhasználói egyedi átírás figyelése
    propFurnishingHuf.addEventListener('input', () => {
        userCustomFurnishing = true;
        triggerPythonCalculations();
    });
    rentMonthlyHuf.addEventListener('input', () => {
        userCustomRent = true;
        triggerPythonCalculations();
    });
    rentUtilitiesHuf.addEventListener('input', () => {
        userCustomUtilities = true;
        triggerPythonCalculations();
    });

    // Reset javaslat gombok (visszaállítja a Python algoritmus ajánlását)
    if (btnResetPrice) {
        btnResetPrice.addEventListener('click', (e) => {
            e.preventDefault();
            userCustomPrice = false;
            runPythonCalculations();
        });
    }
    if (btnResetFurnishing) {
        btnResetFurnishing.addEventListener('click', (e) => {
            e.preventDefault();
            userCustomFurnishing = false;
            runPythonCalculations();
        });
    }
    if (btnResetRent) {
        btnResetRent.addEventListener('click', (e) => {
            e.preventDefault();
            userCustomRent = false;
            runPythonCalculations();
        });
    }
    if (btnResetUtilities) {
        btnResetUtilities.addEventListener('click', (e) => {
            e.preventDefault();
            userCustomUtilities = false;
            runPythonCalculations();
        });
    }

    // --- 4. Lakat Kapcsolók (City & District) ---

    let cityLocked = true;
    let districtLocked = true;

    btnToggleCityLock.addEventListener('click', () => {
        cityLocked = !cityLocked;
        propCity.disabled = cityLocked;
        if (cityLocked) {
            iconLockCity.className = 'bi bi-lock-fill text-danger';
            badgeCityStatus.innerHTML = '<i class="bi bi-lock-fill"></i> Zárolva';
            badgeCityStatus.className = 'badge bg-danger-subtle text-danger p-1';
        } else {
            iconLockCity.className = 'bi bi-unlock-fill text-success';
            badgeCityStatus.innerHTML = '<i class="bi bi-unlock-fill"></i> Feloldva';
            badgeCityStatus.className = 'badge bg-success-subtle text-success p-1';
            propCity.focus();
        }
    });

    btnToggleDistrictLock.addEventListener('click', () => {
        districtLocked = !districtLocked;
        propDistrict.disabled = districtLocked;
        if (districtLocked) {
            iconLockDistrict.className = 'bi bi-lock-fill text-danger';
            badgeDistrictStatus.innerHTML = '<i class="bi bi-lock-fill"></i> Zárolva';
            badgeDistrictStatus.className = 'badge bg-danger-subtle text-danger p-1';
        } else {
            iconLockDistrict.className = 'bi bi-unlock-fill text-success';
            badgeDistrictStatus.innerHTML = '<i class="bi bi-unlock-fill"></i> Feloldva';
            badgeDistrictStatus.className = 'badge bg-success-subtle text-success p-1';
            propDistrict.focus();
        }
    });

    // --- 5. Kétirányú Szinkronizációk és Python hívások ---

    // A) Méret & m² ár -> Vételár
    function updatePriceFromSqm() {
        const size = parseFloat(propSizeSqm.value) || 0;
        const priceSqm = parseCleanNumber(propPriceSqm.value);
        const total = Math.round(size * priceSqm);
        propPriceTotal.value = formatWithDots(total);

        updateLawyerFeeFromPct();
        updateLoanFromDownPaymentPct();
        triggerPythonCalculations();
    }

    // Vételár -> m² ár
    function updateSqmFromTotalPrice() {
        const size = parseFloat(propSizeSqm.value) || 1;
        const total = parseCleanNumber(propPriceTotal.value);
        propPriceSqm.value = formatWithDots(Math.round(total / size));

        updateLawyerFeeFromPct();
        updateLoanFromDownPaymentPct();
        triggerPythonCalculations();
    }

    // B) Ügyvédi díj: Százalék -> Forint
    function updateLawyerFeeFromPct() {
        const total = parseCleanNumber(propPriceTotal.value);
        const pct = parseFloat(propLawyerPct.value) || 0;
        propLawyerHuf.value = formatWithDots(Math.round(total * (pct / 100.0)));
        triggerPythonCalculations();
    }

    // Ügyvédi díj: Forint -> Százalék
    function updateLawyerFeeFromHuf() {
        const total = parseCleanNumber(propPriceTotal.value) || 1;
        const huf = parseCleanNumber(propLawyerHuf.value);
        const pct = (huf / total) * 100.0;
        propLawyerPct.value = pct.toFixed(2);
        triggerPythonCalculations();
    }

    // C) Önerő: Százalék -> Forint és Hitelösszeg
    function updateLoanFromDownPaymentPct() {
        const total = parseCleanNumber(propPriceTotal.value);
        const pct = parseFloat(loanDownPaymentPct.value) || 0;
        const downHuf = Math.round(total * (pct / 100.0));
        loanDownPaymentHuf.value = formatWithDots(downHuf);
        rngDownPayment.value = Math.round(pct);
        lblDownPaymentBadge.textContent = `${pct}% önerő`;

        const loanAmount = Math.max(0, total - downHuf);
        loanAmountHuf.value = formatWithDots(loanAmount);
        triggerPythonCalculations();
    }

    // Önerő: Forint -> Százalék és Hitelösszeg
    function updateLoanFromDownPaymentHuf() {
        const total = parseCleanNumber(propPriceTotal.value) || 1;
        const downHuf = parseCleanNumber(loanDownPaymentHuf.value);
        const pct = Math.min(100, Math.max(0, (downHuf / total) * 100.0));
        loanDownPaymentPct.value = pct.toFixed(1);
        rngDownPayment.value = Math.round(pct);
        lblDownPaymentBadge.textContent = `${pct.toFixed(1)}% önerő`;

        const loanAmount = Math.max(0, total - downHuf);
        loanAmountHuf.value = formatWithDots(loanAmount);
        triggerPythonCalculations();
    }

    // Hitelösszeg közvetlen átírása
    function updateDownPaymentFromLoanAmount() {
        const total = parseCleanNumber(propPriceTotal.value);
        const loan = parseCleanNumber(loanAmountHuf.value);
        const downHuf = Math.max(0, total - loan);
        loanDownPaymentHuf.value = formatWithDots(downHuf);
        const pct = total > 0 ? (downHuf / total) * 100.0 : 0;
        loanDownPaymentPct.value = pct.toFixed(1);
        rngDownPayment.value = Math.round(pct);
        lblDownPaymentBadge.textContent = `${pct.toFixed(1)}% önerő`;
        triggerPythonCalculations();
    }

    // Futamidő gyorsgombok
    btnTerms.forEach(btn => {
        btn.addEventListener('click', () => {
            btnTerms.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            loanTermYears.value = btn.dataset.term;
            triggerPythonCalculations();
        });
    });

    loanTermYears.addEventListener('input', () => {
        const term = loanTermYears.value;
        btnTerms.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.term === term);
        });
        triggerPythonCalculations();
    });

    // Befektetési hozam csúszka szinkron
    rngInvReturn.addEventListener('input', (e) => {
        invReturnPct.value = parseFloat(e.target.value).toFixed(2);
        lblInvReturnBadge.textContent = `${invReturnPct.value}%`;
        triggerPythonCalculations();
    });

    invReturnPct.addEventListener('input', (e) => {
        rngInvReturn.value = e.target.value;
        lblInvReturnBadge.textContent = `${parseFloat(e.target.value || 0).toFixed(2)}%`;
        triggerPythonCalculations();
    });

    rngPropGrowth.addEventListener('input', (e) => {
        lblPropGrowthBadge.textContent = `${parseFloat(e.target.value || 0).toFixed(1)}%`;
        triggerPythonCalculations();
    });

    rngRentInflation.addEventListener('input', (e) => {
        lblRentInflationBadge.textContent = `${parseFloat(e.target.value || 0).toFixed(1)}%`;
        triggerPythonCalculations();
    });

    const chkTbsz = document.getElementById('chk_tbsz_enabled');
    if (chkTbsz) chkTbsz.addEventListener('change', triggerPythonCalculations);

    // Eseményfigyelők mezőváltozásokra
    propType.addEventListener('change', triggerPythonCalculations);
    if (propCondition) {
        propCondition.addEventListener('change', triggerPythonCalculations);
    }
    propRooms.addEventListener('change', triggerPythonCalculations);
    propSizeSqm.addEventListener('input', updatePriceFromSqm);
    propPriceSqm.addEventListener('input', () => {
        userCustomPrice = true;
        updatePriceFromSqm();
    });
    propPriceTotal.addEventListener('input', () => {
        userCustomPrice = true;
        updateSqmFromTotalPrice();
    });
    propCity.addEventListener('input', triggerPythonCalculations);
    propDistrict.addEventListener('input', triggerPythonCalculations);

    propLawyerPct.addEventListener('input', updateLawyerFeeFromPct);
    propLawyerHuf.addEventListener('input', updateLawyerFeeFromHuf);

    loanDownPaymentPct.addEventListener('input', updateLoanFromDownPaymentPct);
    rngDownPayment.addEventListener('input', (e) => {
        loanDownPaymentPct.value = e.target.value;
        updateLoanFromDownPaymentPct();
    });
    loanDownPaymentHuf.addEventListener('input', updateLoanFromDownPaymentHuf);
    loanAmountHuf.addEventListener('input', updateDownPaymentFromLoanAmount);

    [loanInterestPct, loanOtherFeesHuf, loanMonthlyPayment].forEach(el => {
        el.addEventListener('input', triggerPythonCalculations);
    });

    // --- 6. Form Adatok Összegyűjtése ---
    function collectFormData() {
        const manualPmtStr = loanMonthlyPayment.value.trim();
        const manualPmt = manualPmtStr !== "" ? parseCleanNumber(manualPmtStr) : null;

        return {
            property: {
                city: propCity.value.trim(),
                district: propDistrict.value.trim(),
                location: `${propCity.value.trim()}, ${propDistrict.value.trim()}`,
                property_type: propType.value,
                condition: propCondition ? propCondition.value : "Jó állapotú",
                size_sqm: parseFloat(propSizeSqm.value) || 0,
                room_count: parseFloat(propRooms.value) || 1,
                price_total_huf: parseCleanNumber(propPriceTotal.value),
                price_per_sqm_huf: parseCleanNumber(propPriceSqm.value),
                lawyer_fee_pct: parseFloat(propLawyerPct.value) || 0,
                lawyer_fee_huf: parseCleanNumber(propLawyerHuf.value),
                furnishing_cost_huf: parseCleanNumber(propFurnishingHuf.value),
                other_info: propOtherInfo ? propOtherInfo.value.trim() : ""
            },
            loan: {
                down_payment_pct: parseFloat(loanDownPaymentPct.value) || 0,
                down_payment_huf: parseCleanNumber(loanDownPaymentHuf.value),
                loan_amount_huf: parseCleanNumber(loanAmountHuf.value),
                loan_term_years: parseInt(loanTermYears.value) || 20,
                interest_rate_annual_pct: parseFloat(loanInterestPct.value) || 0,
                other_fees_huf: parseCleanNumber(loanOtherFeesHuf.value),
                monthly_payment_huf: manualPmt,
                other_info: loanOtherInfo ? loanOtherInfo.value.trim() : ""
            },
            rent: {
                monthly_rent_huf: parseCleanNumber(rentMonthlyHuf.value),
                monthly_utilities_huf: parseCleanNumber(rentUtilitiesHuf.value),
                other_info: rentOtherInfo ? rentOtherInfo.value.trim() : ""
            },
            investment: {
                expected_return_annual_pct: parseFloat(invReturnPct.value) || 0,
                tbsz_enabled: document.getElementById('chk_tbsz_enabled') ? document.getElementById('chk_tbsz_enabled').checked : true,
                property_growth_pct: parseFloat(rngPropGrowth ? rngPropGrowth.value : 5.0),
                rent_inflation_pct: parseFloat(rngRentInflation ? rngRentInflation.value : 4.0),
                other_info: invOtherInfo ? invOtherInfo.value.trim() : ""
            }
        };
    }

    // --- 7. Gemini AI Elemzés Renderelése ---
    function renderGeminiAnalysis(analysis) {
        if (!analysis || !cardGeminiAnalysis || !containerGeminiResults) return;

        if (badgeGeminiModel) {
            badgeGeminiModel.textContent = analysis.model_used || 'Gemini AI';
        }

        const overall = analysis.overall_summary || 'A megadott egyedi információk sikeresen rögzítésre kerültek.';
        const ev = analysis.evaluations || {};

        const sections = [
            {
                key: 'property',
                title: '1. Lakás & Ingatlan',
                icon: 'bi-house-door-fill',
                color: 'primary',
                data: ev.property || {}
            },
            {
                key: 'loan',
                title: '2. Hitel & Finanszírozás',
                icon: 'bi-bank2',
                color: 'success',
                data: ev.loan || {}
            },
            {
                key: 'rent',
                title: '3. Albérlet & Rezsi',
                icon: 'bi-key-fill',
                color: 'warning',
                data: ev.rent || {}
            },
            {
                key: 'investment',
                title: '4. Befektetés & TBSZ',
                icon: 'bi-piggy-bank-fill',
                color: 'info',
                data: ev.investment || {}
            }
        ];

        function getRelevanceBadge(score) {
            if (!score || score <= 0) {
                return `<span class="badge bg-secondary p-1 px-2" style="font-size:0.75rem;">0/10 (Nincs adat)</span>`;
            }
            if (score >= 8) {
                return `<span class="badge bg-danger p-1 px-2 fw-bold" style="font-size:0.75rem;"><i class="bi bi-exclamation-triangle-fill me-1"></i>${score}/10 - Kiemelt hatás</span>`;
            }
            if (score >= 5) {
                return `<span class="badge bg-warning text-dark p-1 px-2 fw-bold" style="font-size:0.75rem;"><i class="bi bi-info-circle-fill me-1"></i>${score}/10 - Közepes hatás</span>`;
            }
            return `<span class="badge bg-info text-dark p-1 px-2 fw-bold" style="font-size:0.75rem;"><i class="bi bi-info-circle me-1"></i>${score}/10 - Csekély hatás</span>`;
        }

        let cardsHtml = '';
        let hasAnyData = false;

        sections.forEach(s => {
            const item = s.data;
            const score = item.relevance_score || 0;
            const isProvided = item.provided !== false && score > 0;
            
            // Ha nincs adat az adott szekcióhoz, akkor azt nem jelenítjük meg
            if (!isProvided) {
                return;
            }
            
            hasAnyData = true;
            
            const category = item.category || 'Standard tényező';
            const impact = item.impact_analysis || 'Alapértelmezett modell érvényesül.';
            const rec = item.quantitative_recommendation || 'Nincs szükség korrekcióra.';

            cardsHtml += `
                <div class="col-md-6">
                    <div class="card h-100 border border-secondary-subtle shadow-sm">
                        <div class="card-header bg-light d-flex justify-content-between align-items-center py-2">
                            <span class="fw-bold text-${s.color} small">
                                <i class="bi ${s.icon} me-1"></i>${s.title}
                            </span>
                            ${getRelevanceBadge(score)}
                        </div>
                        <div class="card-body p-3">
                            <div class="mb-2">
                                <span class="badge bg-secondary-subtle text-dark border small">${category}</span>
                            </div>
                            <div class="mb-3">
                                <div class="small fw-bold text-dark mb-1">
                                    <i class="bi bi-graph-up-arrow me-1 text-primary"></i>Hogyan szól bele a számolásba:
                                </div>
                                <p class="small mb-0 text-muted" style="line-height: 1.45; font-size: 0.82rem;">
                                    ${impact}
                                </p>
                            </div>
                            <div class="p-2 bg-light rounded border border-info-subtle">
                                <div class="small fw-bold text-info mb-1">
                                    <i class="bi bi-calculator me-1"></i>Kvantitatív korrekciós javaslat:
                                </div>
                                <p class="small mb-0 text-dark" style="line-height: 1.4; font-size: 0.8rem;">
                                    ${rec}
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });

        // Ha egyetlen szekcióhoz sincs adat, elrejtjük a teljes kártyát
        if (!hasAnyData) {
            cardGeminiAnalysis.classList.add('d-none');
            return;
        }

        cardGeminiAnalysis.classList.remove('d-none');

        containerGeminiResults.innerHTML = `
            <div class="alert alert-dark border-secondary p-3 mb-4 shadow-sm">
                <div class="d-flex align-items-start gap-3">
                    <div class="fs-2 text-warning lh-1 mt-1">
                        <i class="bi bi-stars"></i>
                    </div>
                    <div>
                        <h6 class="fw-bold text-white mb-1">
                            <i class="bi bi-robot me-1 text-warning"></i>Átfogó Kvantitatív Szakértői Értékelés (Gemini AI)
                        </h6>
                        <p class="mb-0 text-light small" style="line-height: 1.5; font-size: 0.85rem;">
                            ${overall}
                        </p>
                    </div>
                </div>
            </div>
            <div class="row g-3">
                ${cardsHtml}
            </div>
        `;
    }

    // --- 8. Szerver Adatmentés (POST /api/inputs) ---
    async function saveInputsToServer() {
        const payload = collectFormData();

        // UI töltési állapot kijelzés
        const originalTopHtml = btnSaveTop.innerHTML;
        const btnRunSimulation = document.getElementById('btnRunSimulation');
        let originalRunHtml = '';
        if (btnRunSimulation) {
            originalRunHtml = btnRunSimulation.innerHTML;
            btnRunSimulation.disabled = true;
            btnRunSimulation.innerHTML = '<span class="spinner-border spinner-border-sm me-1" role="status"></span> Gemini AI elemzés futtatása...';
        }
        
        btnSaveTop.disabled = true;
        btnSaveTop.innerHTML = '<span class="spinner-border spinner-border-sm me-1" role="status"></span> Elemzés...';

        // Gemini kártya megjelenítése és spinner
        if (cardGeminiAnalysis && containerGeminiResults) {
            cardGeminiAnalysis.classList.remove('d-none');
            containerGeminiResults.innerHTML = `
                <div class="text-center py-4 text-muted">
                    <div class="spinner-border text-warning me-2" role="status"></div>
                    <span class="fw-bold text-dark">Gemini AI szakértői elemzés folyamatban...</span>
                    <p class="small text-muted mt-2 mb-0">A 4 kiegészítő információ relevanciájának és DCF modellbeli kihatásának vizsgálata</p>
                </div>
            `;
        }

        try {
            const response = await fetch('/api/inputs', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const result = await response.json();
            if (response.ok) {
                showAlert('Sikeres mentés & AI elemzés!', 'A bemeneti paraméterek és a Gemini szakértői értékelés rögzítésre kerültek.', 'success');
                if (result.gemini_analysis) {
                    renderGeminiAnalysis(result.gemini_analysis);
                }
                if (result.gemini_analysis && result.gemini_analysis.evaluations) {
                    currentAiEvaluations = result.gemini_analysis.evaluations;
                }
                if (result.ai_adjusted_suggestions) {
                    applyAiAdjustedSuggestionsToUI(result.ai_adjusted_suggestions);
                }
            } else {
                showAlert('Hiba a mentés során!', result.message || 'Ismeretlen hiba történt.', 'danger');
            }
        } catch (err) {
            showAlert('Hálózati hiba!', 'Nem sikerült elérni a Flask backend szervert.', 'danger');
            console.error(err);
        } finally {
            btnSaveTop.disabled = false;
            btnSaveTop.innerHTML = originalTopHtml;
            if (btnRunSimulation) {
                btnRunSimulation.disabled = false;
                btnRunSimulation.innerHTML = originalRunHtml;
            }
        }
    }

    async function loadInputsFromServer() {
        try {
            const response = await fetch('/api/inputs');
            if (response.ok) {
                const res = await response.json();
                const data = res.data;
                const inputs = data.inputs || data;

                populateForm(inputs);

                // Ha van korábbi mentett elemzés az adatrekordban
                if (data.gemini_analysis) {
                    renderGeminiAnalysis(data.gemini_analysis);
                }
                if (data.gemini_analysis && data.gemini_analysis.evaluations) {
                    currentAiEvaluations = data.gemini_analysis.evaluations;
                }
                if (data.ai_adjusted_suggestions) {
                    applyAiAdjustedSuggestionsToUI(data.ai_adjusted_suggestions);
                }

                // Felhasználói kérés: Az 'Egyéb' szöveges cellák legyenek mindig teljesen üresek oldalbetöltéskor és alapértékre állításkor!
                if (propOtherInfo) propOtherInfo.value = "";
                if (loanOtherInfo) loanOtherInfo.value = "";
                if (rentOtherInfo) rentOtherInfo.value = "";
                if (invOtherInfo) invOtherInfo.value = "";
            }
        } catch (err) {
            console.error("Nem sikerült lekérni a mentett adatokat:", err);
        }
    }

    function populateForm(data) {
        if (!data) return;

        if (data.property) {
            if (data.property.city) propCity.value = data.property.city;
            if (data.property.district) propDistrict.value = data.property.district;
            propType.value = data.property.property_type || propType.value;
            propSizeSqm.value = data.property.size_sqm ?? propSizeSqm.value;
            propRooms.value = (data.property.room_count ?? propRooms.value).toFixed(1);
            propPriceTotal.value = formatWithDots(data.property.price_total_huf ?? 80600000);
            propPriceSqm.value = formatWithDots(data.property.price_per_sqm_huf ?? 1550000);
            propLawyerPct.value = data.property.lawyer_fee_pct ?? 1.0;
            propLawyerHuf.value = formatWithDots(data.property.lawyer_fee_huf ?? 806000);

            if (data.property.furnishing_cost_huf !== undefined) {
                propFurnishingHuf.value = formatWithDots(data.property.furnishing_cost_huf);
            }
            if (propOtherInfo) {
                propOtherInfo.value = data.property.other_info || "";
            }
        }

        if (data.loan) {
            loanDownPaymentPct.value = data.loan.down_payment_pct ?? 25;
            loanDownPaymentHuf.value = formatWithDots(data.loan.down_payment_huf ?? 20150000);
            rngDownPayment.value = Math.round(data.loan.down_payment_pct ?? 25);
            loanAmountHuf.value = formatWithDots(data.loan.loan_amount_huf ?? 60450000);
            loanTermYears.value = data.loan.loan_term_years ?? 20;
            loanInterestPct.value = data.loan.interest_rate_annual_pct ?? 6.5;
            loanOtherFeesHuf.value = formatWithDots(data.loan.other_fees_huf ?? 120000);
            loanMonthlyPayment.value = data.loan.monthly_payment_huf ? formatWithDots(data.loan.monthly_payment_huf) : '';

            btnTerms.forEach(btn => {
                btn.classList.toggle('active', btn.dataset.term === String(data.loan.loan_term_years));
            });

            if (loanOtherInfo) {
                loanOtherInfo.value = data.loan.other_info || "";
            }
        }

        if (data.rent) {
            if (data.rent.monthly_rent_huf !== undefined) {
                rentMonthlyHuf.value = formatWithDots(data.rent.monthly_rent_huf);
            }
            if (data.rent.monthly_utilities_huf !== undefined) {
                rentUtilitiesHuf.value = formatWithDots(data.rent.monthly_utilities_huf);
            }
            if (rentOtherInfo) {
                rentOtherInfo.value = data.rent.other_info || "";
            }
        }

        if (data.investment) {
            invReturnPct.value = data.investment.expected_return_annual_pct ?? 7.0;
            rngInvReturn.value = invReturnPct.value;
            lblInvReturnBadge.textContent = `${parseFloat(invReturnPct.value).toFixed(2)}%`;
            
            if (data.investment.property_growth_pct !== undefined && rngPropGrowth) {
                rngPropGrowth.value = data.investment.property_growth_pct;
                lblPropGrowthBadge.textContent = `${parseFloat(rngPropGrowth.value).toFixed(1)}%`;
            }
            if (data.investment.rent_inflation_pct !== undefined && rngRentInflation) {
                rngRentInflation.value = data.investment.rent_inflation_pct;
                lblRentInflationBadge.textContent = `${parseFloat(rngRentInflation.value).toFixed(1)}%`;
            }

            if (invOtherInfo) {
                invOtherInfo.value = data.investment.other_info || "";
            }
        }

        runPythonCalculations();
    }

    function showAlert(title, message, type = 'success') {
        statusAlertTitle.textContent = title;
        statusAlertMessage.textContent = message;
        statusAlert.className = `alert alert-${type} alert-dismissible fade show mb-3 shadow-sm`;
        statusAlert.classList.remove('d-none');
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    btnCloseAlert.addEventListener('click', () => {
        statusAlert.classList.add('d-none');
    });

    const btnRunSimulation = document.getElementById('btnRunSimulation');
    const resultsSection = document.getElementById('resultsSection');

    btnSaveTop.addEventListener('click', () => {
        saveInputsToServer();
        resultsSection.classList.remove('d-none');
    });
    
    if (btnRunSimulation) {
        btnRunSimulation.addEventListener('click', () => {
            saveInputsToServer();
            resultsSection.classList.remove('d-none');
            if (cardAiSummary) cardAiSummary.classList.remove('d-none');
            
            // Finom görgetés az eredményekhez egy kis késleltetéssel
            setTimeout(() => {
                resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }, 100);
        });
    }

    btnResetDefaults.addEventListener('click', async () => {
        if (confirm('Biztosan visszaállítod az eredeti alapértékeket?')) {
            try {
                await fetch('/api/inputs', { method: 'DELETE' });
            } catch (e) {
                console.error('Reset failed', e);
            }
            window.location.reload();
        }
    });

    const btnGenerateSummary = document.getElementById('btnGenerateSummary');
    const containerAiSummary = document.getElementById('containerAiSummary');
    const cardAiSummary = document.getElementById('cardAiSummary');

    if (btnGenerateSummary) {
        btnGenerateSummary.addEventListener('click', async () => {
            btnGenerateSummary.disabled = true;
            btnGenerateSummary.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Generálás...';
            containerAiSummary.innerHTML = '<div class="text-center py-3 text-muted"><div class="spinner-border text-info spinner-border-sm me-2"></div> AI elemzés készül...</div>';
            
            try {
                const payload = collectFormData();
                if (currentAiEvaluations) {
                    payload.ai_evaluations = currentAiEvaluations;
                }
                
                // 1. Calculate to get the latest simulation results
                const calcRes = await fetch('/api/calculate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                
                if (!calcRes.ok) throw new Error("Calculation failed");
                const calcData = await calcRes.json();
                
                // 2. Request the summary
                const sumRes = await fetch('/api/generate_summary', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        inputs: payload,
                        simulation: calcData.raw.simulation
                    })
                });
                
                if (!sumRes.ok) throw new Error("Summary generation failed");
                const sumData = await sumRes.json();
                
                containerAiSummary.innerHTML = `<p class="mb-0 text-dark" style="font-size: 0.95rem; line-height: 1.6;">${sumData.summary_text.replace(/\n/g, '<br>')}</p>`;
                
            } catch (err) {
                console.error(err);
                containerAiSummary.innerHTML = '<p class="text-danger mb-0">Hiba történt az összefoglaló generálása során.</p>';
            } finally {
                btnGenerateSummary.disabled = false;
                btnGenerateSummary.innerHTML = '<i class="bi bi-magic me-1"></i>Újragenerálás';
            }
        });
    }

    // --- 9. Vagyonfelhalmozási Chart.js Rajzolás ---
    let wealthChartInstance = null;
    let cashflowChartInstance = null;
    let equityChartInstance = null;
    
    const badgeBreakEven = document.getElementById('badgeBreakEven');

    function renderWealthChart(simulation) {
        if (!simulation || !simulation.trajectories) return;

        const summary = simulation.summary;
        const traj = simulation.trajectories;

        // Break-even badge frissítése
        if (badgeBreakEven) {
            if (summary.break_even_month) {
                badgeBreakEven.textContent = `Megtérülés: ${summary.break_even_year} év (${summary.break_even_month}. hónap)`;
                badgeBreakEven.className = "badge bg-success fs-6 py-2";
            } else {
                badgeBreakEven.textContent = "Bérlés (ETF) jobban megéri a 30. év végén is!";
                badgeBreakEven.className = "badge bg-danger fs-6 py-2";
            }
        }

        const ctxWealth = document.getElementById('wealthChart');
        const ctxCashflow = document.getElementById('cashflowChart');
        const ctxEquity = document.getElementById('equityChart');

        // Pusztítsuk el a régi grafikonokat
        if (wealthChartInstance) wealthChartInstance.destroy();
        if (cashflowChartInstance) cashflowChartInstance.destroy();
        if (equityChartInstance) equityChartInstance.destroy();

        // Közös opciók
        const commonOptions = {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 0 }, // Kikapcsolja a pattogó animációt csúszkahúzáskor
            interaction: { mode: 'index', intersect: false },
            plugins: {
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return (context.dataset.label || '') + ': ' + formatHUF(context.parsed.y);
                        },
                        title: function(context) { return context[0].label + '. év'; }
                    }
                },
                legend: { position: 'bottom', labels: { usePointStyle: true, boxWidth: 8 } }
            },
            scales: {
                x: { ticks: { maxTicksLimit: 15 } },
                y: { ticks: { callback: function(value) { return (value / 1000000).toFixed(0) + ' M Ft'; } } }
            }
        };

        // 1. Vagyon Chart
        if (ctxWealth) {
            wealthChartInstance = new Chart(ctxWealth, {
                type: 'line',
                data: {
                    labels: traj.year,
                    datasets: [
                        {
                            label: 'Saját Lakás (Nettó Vagyon)', data: traj.buy_net_worth,
                            borderColor: '#0d6efd', backgroundColor: 'rgba(13, 110, 253, 0.1)',
                            borderWidth: 2, pointRadius: 0, pointHitRadius: 10, fill: true, tension: 0.1
                        },
                        {
                            label: 'Bérlés + ETF (Nettó Vagyon)', data: traj.rent_net_worth,
                            borderColor: '#ffc107', backgroundColor: 'rgba(255, 193, 7, 0.1)',
                            borderWidth: 2, pointRadius: 0, pointHitRadius: 10, fill: true, tension: 0.1
                        }
                    ]
                },
                options: Object.assign({}, commonOptions, {
                    scales: {
                        x: commonOptions.scales.x,
                        y: Object.assign({}, commonOptions.scales.y, { title: { display: true, text: 'Nettó Vagyon (HUF)' } })
                    }
                })
            });
        }

        // 2. Cash-Flow Chart
        if (ctxCashflow) {
            cashflowChartInstance = new Chart(ctxCashflow, {
                type: 'line',
                data: {
                    labels: traj.year,
                    datasets: [
                        {
                            label: 'Tulajdonos havi kiadása (Törlesztő + Rezsi + Amortizáció)', data: traj.monthly_buy_outflow,
                            borderColor: '#dc3545', backgroundColor: 'transparent',
                            borderWidth: 2, pointRadius: 0, pointHitRadius: 10, tension: 0.1
                        },
                        {
                            label: 'Bérlő havi kiadása (Bérleti díj + Rezsi)', data: traj.monthly_rent_outflow,
                            borderColor: '#198754', backgroundColor: 'transparent',
                            borderWidth: 2, pointRadius: 0, pointHitRadius: 10, tension: 0.1
                        }
                    ]
                },
                options: Object.assign({}, commonOptions, {
                    scales: {
                        x: commonOptions.scales.x,
                        y: { ticks: { callback: function(value) { return formatWithDots(value) + ' Ft'; } } }
                    }
                })
            });
        }

        // 3. Equity vs Debt Chart
        if (ctxEquity) {
            equityChartInstance = new Chart(ctxEquity, {
                type: 'line',
                data: {
                    labels: traj.year,
                    datasets: [
                        {
                            label: 'Ingatlan Piaci Értéke', data: traj.property_market_value,
                            borderColor: '#0dcaf0', backgroundColor: 'rgba(13, 202, 240, 0.1)',
                            borderWidth: 2, pointRadius: 0, pointHitRadius: 10, fill: true, tension: 0.1
                        },
                        {
                            label: 'Fennálló Banki Tartozás', data: traj.remaining_loan_balance,
                            borderColor: '#dc3545', backgroundColor: 'rgba(220, 53, 69, 0.1)',
                            borderWidth: 2, pointRadius: 0, pointHitRadius: 10, fill: true, tension: 0.1
                        }
                    ]
                },
                options: Object.assign({}, commonOptions, {
                    scales: {
                        x: commonOptions.scales.x,
                        y: Object.assign({}, commonOptions.scales.y, { title: { display: true, text: 'HUF' } })
                    }
                })
            });
        }
    }

    // --- Új: Heatmap Renderelése ---
    function renderHeatmap(sensitivity) {
        const container = document.getElementById('heatmapContainer');
        if (!container || !sensitivity) return;
        
        const etfRates = sensitivity.etf_rates_pct;
        const propRates = sensitivity.property_growth_rates_pct;
        const matrix = sensitivity.wealth_difference_matrix;
        
        let html = '<div class="table-responsive"><table class="table table-sm table-bordered text-center align-middle" style="font-size: 0.85rem;">';
        
        // Fejléc
        html += '<thead class="table-light"><tr>';
        html += '<th><div class="small text-muted">Ingatlan drágulás \u2193</div><div class="small text-muted">ETF hozam \u2192</div></th>';
        etfRates.forEach(etf => {
            html += `<th class="fw-bold">${etf}%</th>`;
        });
        html += '</tr></thead><tbody>';
        
        // Sorok
        propRates.forEach((prop, i) => {
            html += `<tr><th class="table-light fw-bold text-nowrap">${prop}% / év</th>`;
            
            matrix[i].forEach(diff => {
                let bgColor, textColor, icon;
                if (diff > 0) {
                    // Saját lakás nyer (Zöld)
                    const intensity = Math.min(1, diff / 50000000);
                    bgColor = `rgba(25, 135, 84, ${0.1 + (intensity * 0.4)})`;
                    textColor = 'text-success';
                    icon = '<i class="bi bi-house-door-fill"></i>';
                } else {
                    // Bérlés nyer (Piros)
                    const intensity = Math.min(1, Math.abs(diff) / 50000000);
                    bgColor = `rgba(220, 53, 69, ${0.1 + (intensity * 0.4)})`;
                    textColor = 'text-danger';
                    icon = '<i class="bi bi-piggy-bank-fill"></i>';
                }
                
                const formattedDiff = formatWithDots(Math.abs(Math.round(diff / 1000000))) + ' M Ft';
                html += `<td style="background-color: ${bgColor};" class="${textColor} fw-bold" title="Különbség: ${formatWithDots(Math.round(diff))} Ft">`;
                html += `<div class="d-flex flex-column align-items-center justify-content-center"><span>${icon}</span><span>+${formattedDiff}</span></div>`;
                html += `</td>`;
            });
            html += '</tr>';
        });
        
        html += '</tbody></table></div>';
        
        // Jelmagyarázat
        html += `
            <div class="d-flex justify-content-center gap-4 mt-2 small text-muted">
                <div><i class="bi bi-house-door-fill text-success"></i> Saját lakás vagyona nagyobb</div>
                <div><i class="bi bi-piggy-bank-fill text-danger"></i> Bérlés + ETF vagyona nagyobb</div>
            </div>
        `;
        
        container.innerHTML = html;
    }

    // --- Új: Dinamikus AI Chat Asszisztens ---
    const btnChatOpen = document.getElementById('btnChatOpen');
    const aiChatWidget = document.getElementById('aiChatWidget');
    const btnChatClose = document.getElementById('btnChatClose');
    const chatWidgetHeader = document.getElementById('chatWidgetHeader');
    const chatInput = document.getElementById('chatInput');
    const btnChatSend = document.getElementById('btnChatSend');
    const chatMessages = document.getElementById('chatMessages');

    let chatHistory = [];

    if (btnChatOpen && aiChatWidget) {
        const toggleChat = () => {
            if (aiChatWidget.style.display === 'none') {
                aiChatWidget.style.display = 'flex';
                btnChatOpen.style.display = 'none';
                chatInput.focus();
            } else {
                aiChatWidget.style.display = 'none';
                btnChatOpen.style.display = 'block';
            }
        };

        btnChatOpen.addEventListener('click', toggleChat);
        btnChatClose.addEventListener('click', toggleChat);
        chatWidgetHeader.addEventListener('click', toggleChat);

        const addMessage = (text, sender) => {
            const isUser = sender === 'user';
            const align = isUser ? 'text-end' : 'text-start';
            const bgClass = isUser ? 'bg-primary text-white' : 'bg-white text-dark border';
            const msgHtml = `
                <div class="mb-2 ${align}">
                    <span class="d-inline-block ${bgClass} p-2 rounded shadow-sm small" style="max-width: 85%;">
                        ${text}
                    </span>
                </div>
            `;
            chatMessages.insertAdjacentHTML('beforeend', msgHtml);
            chatMessages.scrollTop = chatMessages.scrollHeight;
        };

        const applyAiUpdates = (updates) => {
            if (!updates || Object.keys(updates).length === 0) return;
            
            let changed = false;
            if (updates.price_total_huf !== undefined) {
                document.getElementById('prop_price_total_huf').value = formatWithDots(updates.price_total_huf);
                userCustomPrice = true;
                changed = true;
            }
            if (updates.down_payment_pct !== undefined) {
                document.getElementById('loan_down_payment_pct').value = formatWithDots(updates.down_payment_pct);
                document.getElementById('rngDownPayment').value = updates.down_payment_pct;
                changed = true;
            }
            if (updates.loan_term_years !== undefined) {
                document.getElementById('loan_term_years').value = updates.loan_term_years;
                document.querySelectorAll('.btn-term').forEach(btn => {
                    btn.classList.toggle('active', btn.dataset.term === String(updates.loan_term_years));
                });
                changed = true;
            }
            if (updates.interest_rate_annual_pct !== undefined) {
                document.getElementById('loan_interest_rate_annual_pct').value = formatWithDots(updates.interest_rate_annual_pct);
                document.getElementById('rngInterestRate').value = updates.interest_rate_annual_pct;
                changed = true;
            }
            if (updates.monthly_rent_huf !== undefined) {
                document.getElementById('rent_monthly_huf').value = formatWithDots(updates.monthly_rent_huf);
                userCustomRent = true;
                changed = true;
            }
            if (updates.expected_return_annual_pct !== undefined) {
                document.getElementById('inv_return_pct').value = updates.expected_return_annual_pct;
                document.getElementById('rngInvReturn').value = updates.expected_return_annual_pct;
                document.getElementById('lblInvReturnBadge').textContent = `${updates.expected_return_annual_pct}%`;
                changed = true;
            }
            if (updates.property_growth_pct !== undefined) {
                document.getElementById('rngPropGrowth').value = updates.property_growth_pct;
                document.getElementById('lblPropGrowthBadge').textContent = `${updates.property_growth_pct}%`;
                changed = true;
            }

            if (changed) {
                triggerPythonCalculations();
            }
        };

        const sendMessage = async () => {
            const text = chatInput.value.trim();
            if (!text) return;

            addMessage(text, 'user');
            chatHistory.push({ role: 'user', content: text });
            chatInput.value = '';
            
            // Show typing indicator
            const typingId = 'typing-' + Date.now();
            chatMessages.insertAdjacentHTML('beforeend', `
                <div class="mb-2 text-start" id="${typingId}">
                    <span class="d-inline-block bg-white p-2 rounded shadow-sm small text-muted border">
                        <span class="spinner-grow spinner-grow-sm" role="status"></span> Gépel...
                    </span>
                </div>
            `);
            chatMessages.scrollTop = chatMessages.scrollHeight;

            try {
                const currentParams = collectFormData();
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        message: text,
                        history: chatHistory,
                        current_params: currentParams
                    })
                });

                document.getElementById(typingId).remove();

                if (response.ok) {
                    const data = await response.json();
                    
                    if (data.updates && Object.keys(data.updates).length > 0) {
                        applyAiUpdates(data.updates);
                    }
                    
                    if (data.text) {
                        addMessage(data.text, 'model');
                        chatHistory.push({ role: 'model', content: data.text });
                    }
                } else {
                    addMessage('Hiba történt a szerver elérésekor.', 'model');
                }
            } catch (err) {
                document.getElementById(typingId).remove();
                addMessage('Hálózati hiba.', 'model');
                console.error(err);
            }
        };

        btnChatSend.addEventListener('click', sendMessage);
        chatInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });
    }

    // Kezdeti indítás
    loadInputsFromServer();
    runPythonCalculations();
});
