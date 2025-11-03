document.addEventListener('DOMContentLoaded', function() {
    function handleDeleteClick(e) {
        const btn = e.currentTarget;

        // If this button is inside a form (we now prefer form-based POST delete),
        // do not run the AJAX delete handler to avoid double-submits.
        if (btn.closest && btn.closest('form')) return;

        const id = btn.dataset.id;
        if (!id) return;

        if (!confirm('Are you sure you want to delete this saved fertilizer?')) return;

        btn.disabled = true;
        const prev = btn.textContent;
        btn.textContent = 'Deleting...';

        fetch('/delete_dashboard_fertilizer', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id: parseInt(id, 10) })
        })
        .then(resp => {
            if (!resp.ok) return resp.text().then(text => { throw new Error(text || ('Status ' + resp.status)); });
            return resp.json();
        })
        .then(data => {
            if (data && data.status === 'success') {
                const node = document.getElementById('saved-fertilizer-' + id);
                if (node) node.remove();
                alert('Deleted ✅');
            } else {
                throw new Error((data && data.error) || 'Delete failed');
            }
        })
        .catch(err => {
            console.error('Delete error:', err);
            alert('Could not delete. Try again.\n\n' + err.message);
            btn.disabled = false;
            btn.textContent = prev;
        });
    }

    const delBtns = document.querySelectorAll('.delete-fertilizer-btn');
    delBtns.forEach(b => b.addEventListener('click', handleDeleteClick));

    // Fallback information for common fertilizers (used if saved record lacks details)
    const FALLBACK_INFO = {
        'urea': {
            description: 'Urea (46% N) is a high‑nitrogen fertilizer used to correct nitrogen deficiency. It is water‑soluble and widely used for top dressing and broadcasting.',
            manual: '1. Apply as top-dressing or broadcast; 2. Incorporate into soil or irrigate after application to reduce volatilization; 3. Split applications for long-duration crops.',
            safety: 'Wear gloves and eye protection. Avoid skin contact; if contact occurs, wash with soap and water. Store dry and away from children.'
        },
        'dap': {
            description: 'Diammonium Phosphate (DAP, 18-46-0) supplies both phosphorus and nitrogen. It is effective for early root development and crop establishment.',
            manual: '1. Apply near the seed at planting (avoid direct seed contact for sensitive crops); 2. Mix into soil if possible; 3. Use recommended rates based on soil test.',
            safety: 'Avoid inhalation and contact with eyes. Store in a cool dry place. Follow label directions for use and disposal.'
        },
        'muriate of potash': {
            description: 'Muriate of Potash (MOP) is a potassium fertilizer (KCl) commonly used to correct potassium deficiency and improve water regulation in plants.',
            manual: '1. Apply to soil or broadcast as band application; 2. Apply according to crop potassium requirement and soil test results.',
            safety: 'Avoid ingestion and prolonged skin contact. Store away from moisture.'
        },
        'ssp': {
            description: 'Single Super Phosphate (SSP) supplies phosphorus and calcium, useful where soil pH and calcium are considerations.',
            manual: '1. Apply according to soil test; 2. Incorporate into soil where possible to improve P availability.',
            safety: 'Handle with gloves and avoid dust inhalation.'
        },
        'npk': {
            description: 'Balanced NPK blends provide nitrogen, phosphorus and potassium tailored for crop needs. Ratios vary (e.g. 10-26-26).',
            manual: '1. Use blends matched to crop needs; 2. Follow label for split applications where appropriate.',
            safety: 'Follow general fertilizer handling precautions; avoid contact and inhalation.'
        },
        'ammonium sulfate': {
            description: 'Ammonium Sulfate supplies nitrogen and sulfur and is useful in sulfur-deficient soils.',
            manual: '1. Apply as basal or side-dress depending on crop; 2. Adjust pH-sensitive crops carefully.',
            safety: 'Avoid inhalation; wear PPE when handling.'
        }
        // add more entries as needed
    };

    // Updated view handler: uses fallback info when card metadata is empty or generic
    function handleViewClick(e) {
        const btn = e.currentTarget;
        const card = btn.closest('.saved-fertilizer-card');
        if (!card) return;
        const title = card.querySelector('.fert-name') ? card.querySelector('.fert-name').textContent.trim() : 'Fertilizer Details';
        // raw saved values (may be the default "No description..." set in template)
        let description = (card.dataset.description || '').trim();
        let manualRaw = (card.dataset.manual || '').trim();
        let safetyRaw = (card.dataset.safety || '').trim();

        // determine whether fallback usage is allowed for this container
        const outerContainer = card.closest('.saved-fertilizers-container');
        const useFallback = outerContainer ? (outerContainer.dataset.useFallback !== 'false') : true;

        // try lookup in FALLBACK_INFO (exists earlier in file)
        const key = title.toLowerCase();
        let usedFallback = false;

        if (useFallback) {
            if ((!description || /^no description/i.test(description))) {
                if (FALLBACK_INFO[key]) {
                    description = FALLBACK_INFO[key].description;
                    if (!manualRaw) manualRaw = FALLBACK_INFO[key].manual;
                    if (!safetyRaw) safetyRaw = FALLBACK_INFO[key].safety;
                    usedFallback = true;
                } else {
                    // fuzzy match
                    for (const k in FALLBACK_INFO) {
                        if (key.includes(k)) {
                            description = FALLBACK_INFO[k].description;
                            if (!manualRaw) manualRaw = FALLBACK_INFO[k].manual;
                            if (!safetyRaw) safetyRaw = FALLBACK_INFO[k].safety;
                            usedFallback = true;
                            break;
                        }
                    }
                }
            }
        }

        // after attempts, determine source label
        let sourceLabel = 'No information available';
        const hasSaved = card.dataset.description && !/^no description/i.test(card.dataset.description);
        if (hasSaved) sourceLabel = 'Saved data';
        else if (usedFallback) sourceLabel = 'Built-in info (fallback)';
        else sourceLabel = 'None';

        // populate modal elements
        const modal = document.getElementById('fertilizer-modal');
        if (!modal) {
            alert(description + '\n\nManual Steps:\n' + manualRaw + '\n\nSafety:\n' + safetyRaw + '\n\nSource: ' + sourceLabel);
            return;
        }
        document.getElementById('fertilizer-modal-title').textContent = title;
        document.getElementById('fertilizer-modal-description').textContent = description || 'No description available.';
        const srcEl = document.getElementById('fertilizer-modal-source');
        if (srcEl) srcEl.textContent = 'Source: ' + sourceLabel;

        // manual steps: try to split into lines; if single paragraph, put as one li
        const manualList = document.getElementById('fertilizer-modal-manual');
        manualList.innerHTML = '';
        if (manualRaw && manualRaw.trim()) {
            const lines = manualRaw.split(/\r?\n|;|\u2022/).map(s => s.trim()).filter(Boolean);
            if (lines.length) {
                lines.forEach(line => {
                    const li = document.createElement('li');
                    li.textContent = line;
                    manualList.appendChild(li);
                });
            } else {
                const li = document.createElement('li');
                li.textContent = manualRaw;
                manualList.appendChild(li);
            }
        } else {
            const li = document.createElement('li');
            li.textContent = 'No manual steps provided.';
            manualList.appendChild(li);
        }

        // safety: split similarly into bullets
        const safetyList = document.getElementById('fertilizer-modal-safety');
        safetyList.innerHTML = '';
        if (safetyRaw && safetyRaw.trim()) {
            const items = safetyRaw.split(/\r?\n|;|\u2022/).map(s => s.trim()).filter(Boolean);
            items.forEach(it => {
                const li = document.createElement('li');
                li.textContent = it;
                safetyList.appendChild(li);
            });
        } else {
            const li = document.createElement('li');
            li.textContent = 'General precautions: use PPE, avoid contact, follow label instructions.';
            safetyList.appendChild(li);
        }

        // open modal (simple show/hide)
        modal.style.display = 'block';
        modal.setAttribute('aria-hidden', 'false');

        // wire "Find Shops" button inside modal to open maps for this fertilizer
        const mapsBtn = document.getElementById('fertilizer-modal-open-maps');
        if (mapsBtn) {
            mapsBtn.onclick = function() {
                const q = encodeURIComponent(title + ' fertilizer shop near me');
                const url = 'https://www.google.com/maps/search/' + q;
                window.open(url, '_blank');
            };
        }
    }

    // Buy button -> open Google Maps searching for nearby fertilizer shops or specific fertilizer
    function handleBuyClick(e) {
        const btn = e.currentTarget;
        const name = (btn.dataset.name || '').trim();
        const query = name ? encodeURIComponent(name + ' fertilizer shop near me') : 'fertilizer+shops+near+me';
        const url = 'https://www.google.com/maps/search/' + query;
        window.open(url, '_blank');
    }

    // Attach view handlers (re-bind in case script executed after DOM changes)
    const viewBtns = document.querySelectorAll('.open-recommendation');
    viewBtns.forEach(b => {
        // remove existing to avoid double-binding
        b.removeEventListener('click', handleViewClick);
        b.addEventListener('click', handleViewClick);
    });

    // Attach buy handlers
    const buyBtns = document.querySelectorAll('.buy-fertilizer');
    buyBtns.forEach(b => b.addEventListener('click', handleBuyClick));

    // Modal close handlers
    const modal = document.getElementById('fertilizer-modal');
    if (modal) {
        const closeElements = [document.getElementById('fertilizer-modal-close'), document.getElementById('fertilizer-modal-close-2')];
        closeElements.forEach(el => {
            if (el) el.addEventListener('click', function() {
                modal.style.display = 'none';
                modal.setAttribute('aria-hidden', 'true');
            });
        });
        // clicking backdrop closes modal
        const backdrop = modal.querySelector('.modal-backdrop');
        if (backdrop) backdrop.addEventListener('click', function() {
            modal.style.display = 'none';
            modal.setAttribute('aria-hidden', 'true');
        });
    }
});
