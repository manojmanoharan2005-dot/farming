(function () {
    document.addEventListener('DOMContentLoaded', function () {
        const btn = document.getElementById('topToolsBtn');
        const panel = document.getElementById('topToolsPanel');
        if (!btn || !panel) return;

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
        const rateIn = document.getElementById('ttSeedRate');
        const priceIn = document.getElementById('ttSeedPrice');
        const outEl = document.getElementById('ttEstimatorOut');
        const calcBtn = document.getElementById('ttCalcBtn');
        const clearBtn = document.getElementById('ttClearBtn');

        function calcEstimator(){
            const area = Math.max(0, parseFloat(areaIn.value) || 0);
            const rate = Math.max(0, parseFloat(rateIn.value) || 0);
            const price = parseFloat(priceIn.value);
            const seedNeeded = +(area * rate).toFixed(2);
            let html = `<div><strong>Seed required:</strong> ${seedNeeded.toLocaleString()} kg</div>`;
            if (!isNaN(price) && price > 0) {
                const cost = +(seedNeeded * price).toFixed(2);
                html += `<div><strong>Estimated seed cost:</strong> ₹${cost.toLocaleString()}</div>`;
            }
            outEl.innerHTML = html;
        }

        calcBtn?.addEventListener('click', (e) => { e.preventDefault(); calcEstimator(); });
        clearBtn?.addEventListener('click', (e) => {
            e.preventDefault();
            if(areaIn) areaIn.value = '1';
            if(rateIn) rateIn.value = '25';
            if(priceIn) priceIn.value = '';
            outEl.innerHTML = '';
        });

        /* ===== Weather tab ===== */
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
            // q may be city or "lat,lon"
            const url = `https://api.weatherapi.com/v1/current.json?key=${encodeURIComponent(WEATHERAPI_KEY)}&q=${encodeURIComponent(q)}&aqi=no`;
            const res = await fetch(url);
            if (!res.ok) throw new Error('WeatherAPI request failed');
            return res.json();
        }

        async function fetchWeatherFallbackByQ(q) {
            // backend proxy expected to accept ?q=...
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

            // If manual location provided, use it
            const manualQ = (wxLocIn?.value || '').trim();
            if (manualQ) {
                try {
                    // persist manual location
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
                    // try fallback if possible
                    console.warn('Manual location weather failed, trying fallback', err);
                }
            }

            // If user requested geolocation or no manual q, use geolocation
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
                        // geolocation denied / failed: fallback to backend without coords
                        try {
                            if (WEATHERAPI_KEY) {
                                // no coords to supply: try backend instead
                                const j = await fetch('/api/weather');
                                if (!j.ok) throw new Error('no backend');
                                const data = await j.json();
                                renderWeatherData(data);
                            } else {
                                const j = await fetch('/api/weather');
                                if (!j.ok) throw new Error('no backend');
                                const data = await j.json();
                                renderWeatherData(data);
                            }
                        } catch (e) {
                            wxOut.innerHTML = '<div style="color:#b91c1c">Unable to load weather</div>';
                        }
                    }, { timeout: 5000 });
                    return;
                } else {
                    // no geolocation: backend only
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

        // Enter key in location input triggers search
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
