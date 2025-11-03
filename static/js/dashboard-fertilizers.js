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
});
