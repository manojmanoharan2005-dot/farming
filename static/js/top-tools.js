(function () {
    document.addEventListener('DOMContentLoaded', function () {
        const btn = document.getElementById('topToolsBtn');
        const panel = document.getElementById('topToolsPanel');
        if (!btn || !panel) return;

        // Remove any legacy seed-specific inputs that may cause duplicates
        try {
            const legacySeedRate = document.getElementById('ttSeedRate');
            if (legacySeedRate) legacySeedRate.remove();
            const legacySeedPrice = document.getElementById('ttSeedPrice');
            if (legacySeedPrice) legacySeedPrice.remove();
        } catch (e) { /* ignore */ }

        // Toggle panel
        btn.addEventListener('click', (e) => {
            const shown = panel.style.display === 'block';
            panel.style.display = shown ? 'none' : 'block';
            btn.setAttribute('aria-expanded', String(!shown));
        });

        // Close when clicking outside
        document.addEventListener('click', (e) => {
            if (!panel.contains(e.target) && !btn.contains(e.target)) {
                panel.style.display = 'none';
                btn.setAttribute('aria-expanded', 'false');
            }
        });

        // Tab switching
        const tabs = panel.querySelectorAll('.tt-tab');
        tabs.forEach(t => t.addEventListener('click', () => {
            tabs.forEach(x => x.classList.remove('active'));
            t.classList.add('active');
            const tab = t.dataset.tab;
            panel.querySelectorAll('.tt-panel').forEach(p => p.style.display = p.id === 'tt' + tab.charAt(0).toUpperCase() + tab.slice(1) ? 'block' : 'none');
            // Auto-fetch weather when switching to weather tab
            if (tab === 'weather') fetchWeatherForTop();
        }));

        /* ===== Task Estimator ===== */
        const areaIn = document.getElementById('ttArea');
        const rateIn = document.getElementById('ttRate');
        const priceIn = document.getElementById('ttPrice');
        const estimateFor = document.getElementById('ttEstimateFor');
        const rateLabel = document.getElementById('ttRateLabel');
        const priceLabel = document.getElementById('ttPriceLabel');
        const outEl = document.getElementById('ttEstimatorOut');
        const calcBtn = document.getElementById('ttCalcBtn');
        const clearBtn = document.getElementById('ttClearBtn');

        const LS_EST_TYPE = 'top_tools_est_type';
        // restore estimator type
        try { const savedType = localStorage.getItem(LS_EST_TYPE); if (savedType && estimateFor) estimateFor.value = savedType; } catch (e) {}

        function setRateDefaults(type) {
            // set sensible defaults per type and update labels/placeholders
            switch (type) {
                case 'seed':
                    rateIn.value = rateIn.value && +rateIn.value>0 ? rateIn.value : 25;
                    rateLabel.textContent = 'Seed rate (kg/ha)';
                    priceLabel.textContent = 'Seed price (₹/kg) — optional';
                    priceIn.placeholder = '₹ / kg';
                    break;
                case 'fertilizer':
                    rateIn.value = rateIn.value && +rateIn.value>0 ? rateIn.value : 150;
                    rateLabel.textContent = 'Fertilizer (kg/ha)';
                    priceLabel.textContent = 'Fertilizer price (₹/kg) — optional';
                    priceIn.placeholder = '₹ / kg';
                    break;
                case 'labor':
                    rateIn.value = rateIn.value && +rateIn.value>0 ? rateIn.value : 40;
                    rateLabel.textContent = 'Labor (hours/ha)';
                    priceLabel.textContent = 'Labor cost (₹/hour) — optional';
                    priceIn.placeholder = '₹ / hour';
                    break;
                case 'irrigation':
                    rateIn.value = rateIn.value && +rateIn.value>0 ? rateIn.value : 10;
                    rateLabel.textContent = 'Irrigation (hours/ha)';
                    priceLabel.textContent = 'Irrigation cost (₹/hour) — optional';
                    priceIn.placeholder = '₹ / hour';
                    break;
                default:
                    rateIn.value = rateIn.value && +rateIn.value>0 ? rateIn.value : 1;
                    rateLabel.textContent = 'Rate (unit/ha)';
                    priceLabel.textContent = 'Price (₹/unit) — optional';
                    priceIn.placeholder = '₹ / unit';
            }
        }

        function unitForType(type) {
            switch (type) {
                case 'seed':
                case 'fertilizer': return 'kg';
                case 'labor':
                case 'irrigation': return 'hrs';
                default: return 'units';
            }
        }

        function calcEstimator(){
            const type = (estimateFor?.value || 'seed');
            const area = Math.max(0, parseFloat(areaIn.value) || 0);
            const rate = Math.max(0, parseFloat(rateIn.value) || 0);
            const price = parseFloat(priceIn.value);
            const unit = unitForType(type);

            const amountNeeded = +(area * rate).toFixed(2);
            let html = `<div><strong>${amountNeeded.toLocaleString()} ${unit}</strong> required</div>`;
            if (!isNaN(price) && price > 0) {
                const cost = +(amountNeeded * price).toFixed(2);
                html += `<div style="margin-top:6px;"><strong>Estimated cost:</strong> ₹${cost.toLocaleString()}</div>`;
            } else {
                html += `<div style="margin-top:6px;color:#6b7280">Enter price to see estimated cost</div>`;
            }
            outEl.innerHTML = html;
            // persist estimator type
            try { localStorage.setItem(LS_EST_TYPE, type); } catch (e) {}
        }

        function clearEstimator(){
            if(areaIn) areaIn.value = '1';
            if(rateIn) rateIn.value = '';
            if(priceIn) priceIn.value = '';
            outEl.innerHTML = '';
        }

        // initialize labels/defaults on load (ensures "seed price" text only appears for Seed)
        setRateDefaults(estimateFor?.value || 'seed');

        // listeners
        estimateFor?.addEventListener('change', (e) => {
            setRateDefaults(e.target.value);
            outEl.innerHTML = '';
            try { localStorage.setItem(LS_EST_TYPE, e.target.value); } catch (e) {}
        });
        calcBtn?.addEventListener('click', (e) => { e.preventDefault(); calcEstimator(); });
        clearBtn?.addEventListener('click', (e) => { e.preventDefault(); clearEstimator(); });

        /* ===== Weather tab (unchanged) ===== */
        const wxOut = document.getElementById('ttWxOut');
        const wxRefresh = document.getElementById('ttWxRefresh');
        const wxLocIn = document.getElementById('ttWxLocation');
        const wxUseMy = document.getElementById('ttWxUseMyLoc');

        // Read WeatherAPI key from meta tag
        const metaKey = (document.querySelector('meta[name="weatherapi-key"]') || {}).content || '';
        const WEATHERAPI_KEY = metaKey && metaKey.trim() ? metaKey.trim() : null;

        const LS_LOC_KEY = 'top_tools_location';
        // restore saved manual location
        try { const saved = localStorage.getItem(LS_LOC_KEY); if (saved && wxLocIn) wxLocIn.value = saved; } catch (e) {}

        async function fetchWeatherFromWeatherAPIByQ(q) {
            const url = `https://api.weatherapi.com/v1/current.json?key=${encodeURIComponent(WEATHERAPI_KEY)}&q=${encodeURIComponent(q)}&aqi=no`;
            const res = await fetch(url);
            if (!res.ok) throw new Error('WeatherAPI request failed');
            return res.json();
        }

        async function fetchWeatherFallbackByQ(q) {
            const url = q ? `/api/weather?q=${encodeURIComponent(q)}` : '/api/weather';
            const res = await fetch(url);
            if (!res.ok) throw new Error('Backend weather request failed');
            return res.json();
        }

        function renderWeatherData(data) {
            try {
                if (data.current) {
                    const temp = (data.current.temp_c ?? data.current.temp ?? '—');
                    const hum = (data.current.humidity ?? '—');
                    const precip = (data.current.precip_mm ?? data.current.precipitation ?? 0);
                    wxOut.innerHTML = `
                        <div style="display:flex;justify-content:space-between"><span>Temperature</span><strong>${temp}°C</strong></div>
                        <div style="display:flex;justify-content:space-between"><span>Humidity</span><strong>${hum}%</strong></div>
                        <div style="display:flex;justify-content:space-between"><span>Precipitation</span><strong>${precip} mm</strong></div>
                    `;
                    return;
                }
                if (data.temperature !== undefined) {
                    wxOut.innerHTML = `
                        <div style="display:flex;justify-content:space-between"><span>Temperature</span><strong>${data.temperature}°C</strong></div>
                        <div style="display:flex;justify-content:space-between"><span>Humidity</span><strong>${data.humidity ?? '—'}%</strong></div>
                        <div style="display:flex;justify-content:space-between"><span>Rain chance</span><strong>${data.rain_chance ?? '—'}%</strong></div>
                    `;
                    return;
                }
                wxOut.innerHTML = '<div style="color:#b91c1c">Unexpected weather format</div>';
            } catch (err) {
                wxOut.innerHTML = '<div style="color:#b91c1c">Error rendering weather</div>';
                console.error(err);
            }
        }

        async function fetchWeatherForTop(useMyLocation = false) {
            if (!wxOut) return;
            wxOut.innerHTML = '<div>Loading…</div>';

            const manualQ = (wxLocIn?.value || '').trim();
            if (manualQ) {
                try {
                    try { localStorage.setItem(LS_LOC_KEY, manualQ); } catch (e) {}
                    if (WEATHERAPI_KEY) {
                        const j = await fetchWeatherFromWeatherAPIByQ(manualQ);
                        renderWeatherData(j);
                    } else {
                        const j = await fetchWeatherFallbackByQ(manualQ);
                        renderWeatherData(j);
                    }
                    return;
                } catch (err) {
                    console.warn('Manual location weather failed, trying fallback', err);
                }
            }

            if (useMyLocation || !manualQ) {
                if (navigator.geolocation) {
                    navigator.geolocation.getCurrentPosition(async (pos) => {
                        const lat = pos.coords.latitude;
                        const lon = pos.coords.longitude;
                        const q = `${lat},${lon}`;
                        try {
                            if (WEATHERAPI_KEY) {
                                const j = await fetchWeatherFromWeatherAPIByQ(q);
                                renderWeatherData(j);
                            } else {
                                const j = await fetchWeatherFallbackByQ(q);
                                renderWeatherData(j);
                            }
                        } catch (err) {
                            wxOut.innerHTML = '<div style="color:#b91c1c">Unable to load weather</div>';
                            console.error('weather fetch failed', err);
                        }
                    }, async (err) => {
                        try {
                            const j = await fetch('/api/weather');
                            if (!j.ok) throw new Error('no backend');
                            const data = await j.json();
                            renderWeatherData(data);
                        } catch (e) {
                            wxOut.innerHTML = '<div style="color:#b91c1c">Unable to load weather</div>';
                        }
                    }, { timeout: 5000 });
                    return;
                } else {
                    try {
                        const j = await fetch('/api/weather');
                        if (!j.ok) throw new Error('no backend');
                        const data = await j.json();
                        renderWeatherData(data);
                    } catch (err) {
                        wxOut.innerHTML = '<div style="color:#b91c1c">Unable to load weather</div>';
                    }
                }
            }
        }

        wxRefresh?.addEventListener('click', (e) => { e.preventDefault(); fetchWeatherForTop(); });
        wxUseMy?.addEventListener('click', (e) => { e.preventDefault(); if (wxLocIn) wxLocIn.value = ''; fetchWeatherForTop(true); });

        wxLocIn?.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                fetchWeatherForTop();
            }
        });

        // Auto load weather when weather tab is shown
        const observer = new MutationObserver(() => {
            if (panel.style.display === 'block') {
                const active = panel.querySelector('.tt-tab.active')?.dataset.tab;
                if (active === 'weather') fetchWeatherForTop();
            }
        });
        observer.observe(panel, { attributes: true, attributeFilter: ['style'] });
    });
})();
