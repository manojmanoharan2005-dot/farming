(function() {
    const container = document.getElementById('crop-progress-container');
    if (!container) return;

    function ru(n){ return '₹' + (Math.round(n).toLocaleString('en-IN')); }

    function renderProgress(items) {
        if(!Array.isArray(items)) { container.innerHTML = '<div>No progress data</div>'; return; }
        container.innerHTML = items.map(p => {
            const tasksHtml = (p.tasks || []).map((t, i) => {
                const doneClass = t.done ? 'task-done' : '';
                const btn = t.done ? `<button class="btn-mark" disabled>Done</button>`
                                   : `<button class="btn-mark" data-pid="${p.id}" data-ti="${i}">Mark Task Done</button>`;
                return `<div class="task-row ${doneClass}">
                            <div><strong>${t.name}</strong><div style="font-size:.85rem;color:#6b7280">${t.date}</div></div>
                            <div>${btn}</div>
                        </div>`;
            }).join('');

            return `<article class="monitoring-card" id="progress-${p.id}">
                        <div class="meta">
                            <div>
                                <h4 style="margin:0">${p.crop_name}</h4>
                                <div style="font-size:.9rem;color:#6b7280">Start: ${p.start_date} · Harvest: ${p.harvest_date}</div>
                            </div>
                            <div style="text-align:right">
                                <div style="font-weight:700">${p.progress_percent}%</div>
                                <div style="font-size:.85rem;color:#6b7280">${p.status}</div>
                            </div>
                        </div>

                        <div style="margin-top:8px">
                            <div class="progress-bar"><div class="progress-fill" style="width:${p.progress_percent}%"></div></div>
                        </div>

                        <div style="margin-top:8px;font-weight:600">${p.recommendation || ''}</div>

                        <div style="margin-top:10px">${tasksHtml || '<div style=\"color:#6b7280\">No tasks scheduled</div>'}</div>
                     </article>`;
        }).join('');

        // attach event listeners for mark buttons
        Array.from(container.querySelectorAll('.btn-mark')).forEach(btn => {
            if (btn.disabled) return;
            btn.addEventListener('click', function() {
                const pid = this.dataset.pid;
                const ti = parseInt(this.dataset.ti, 10);
                if (!pid || isNaN(ti)) return;
                this.disabled = true;
                fetch('/mark_task_done', {
                    method: 'POST',
                    headers: {'Content-Type':'application/json'},
                    body: JSON.stringify({ progress_id: pid, task_index: ti })
                })
                .then(r => r.json())
                .then(j => {
                    if (j.status === 'success') {
                        // Refresh immediately
                        fetchAndRender();
                    } else {
                        alert('Error: ' + (j.error || JSON.stringify(j)));
                        this.disabled = false;
                    }
                })
                .catch(err => { alert('Network error'); this.disabled = false; });
            });
        });
    }

    function fetchAndRender(){
        fetch('/get_progress', { cache: 'no-store' })
            .then(r => r.json())
            .then(j => renderProgress(j))
            .catch(err => {
                console.error('Progress fetch failed', err);
            });
    }

    // Initial and periodic refresh
    fetchAndRender();
    setInterval(fetchAndRender, 10000);
})();
