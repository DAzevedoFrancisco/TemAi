(function () {
    const modal = document.getElementById('admin-confirm-modal');
    if (!modal) {
        return;
    }

    const overlay = document.getElementById('admin-confirm-overlay');
    const titleEl = document.getElementById('admin-confirm-title');
    const messageEl = document.getElementById('admin-confirm-message');
    const cancelBtn = document.getElementById('admin-confirm-cancel');
    const confirmBtn = document.getElementById('admin-confirm-confirm');
    let pendingForm = null;

    function openModal(form) {
        pendingForm = form;
        titleEl.textContent = form.dataset.confirmTitle || 'Confirmar ação';
        messageEl.textContent = form.dataset.confirmMessage || '';
        modal.hidden = false;
        document.body.style.overflow = 'hidden';
        confirmBtn.focus();
    }

    function closeModal() {
        modal.hidden = true;
        pendingForm = null;
        if (!document.body.classList.contains('dash-nav-open')) {
            document.body.style.overflow = window.innerWidth <= 900 ? 'auto' : '';
        }
    }

    document.querySelectorAll('form[data-confirm-message]').forEach((form) => {
        form.addEventListener('submit', (event) => {
            event.preventDefault();
            openModal(form);
        });
    });

    cancelBtn.addEventListener('click', closeModal);
    overlay.addEventListener('click', closeModal);
    confirmBtn.addEventListener('click', () => {
        if (!pendingForm) {
            return;
        }
        const form = pendingForm;
        closeModal();
        form.submit();
    });

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && !modal.hidden) {
            closeModal();
        }
    });
})();
