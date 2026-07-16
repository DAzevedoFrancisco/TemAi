/* Shared confirm modal for admin + vendor dashboards */
/**
 * Confirmação modal para formulários com data-confirm-message.
 * Compatível com #dash-confirm-modal e #admin-confirm-modal.
 *
 * Importante: o page-loader NÃO deve aparecer no submit inicial —
 * só após o utilizador confirmar (via MobPageLoader.submitForm).
 */
(function () {
    const modal =
        document.getElementById('dash-confirm-modal')
        || document.getElementById('admin-confirm-modal');
    if (!modal) {
        return;
    }

    const overlay =
        document.getElementById('dash-confirm-overlay')
        || document.getElementById('admin-confirm-overlay');
    const titleEl =
        document.getElementById('dash-confirm-title')
        || document.getElementById('admin-confirm-title');
    const messageEl =
        document.getElementById('dash-confirm-message')
        || document.getElementById('admin-confirm-message');
    const cancelBtn =
        document.getElementById('dash-confirm-cancel')
        || document.getElementById('admin-confirm-cancel');
    const confirmBtn =
        document.getElementById('dash-confirm-confirm')
        || document.getElementById('admin-confirm-confirm');

    if (!titleEl || !messageEl || !cancelBtn || !confirmBtn) {
        return;
    }

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

    function bindForm(form) {
        if (!form || form.dataset.confirmBound === 'true') {
            return;
        }
        form.dataset.confirmBound = 'true';
        form.setAttribute('data-no-loader', 'true');
        form.addEventListener('submit', (event) => {
            event.preventDefault();
            event.stopPropagation();
            openModal(form);
        });
    }

    function bindAllConfirmForms(root) {
        (root || document).querySelectorAll('form[data-confirm-message]').forEach(bindForm);
    }

    bindAllConfirmForms(document);

    cancelBtn.addEventListener('click', closeModal);
    overlay?.addEventListener('click', closeModal);

    confirmBtn.addEventListener('click', () => {
        if (!pendingForm) {
            return;
        }
        const form = pendingForm;
        closeModal();
        if (typeof window.MobPageLoader?.submitForm === 'function') {
            window.MobPageLoader.submitForm(form);
        } else if (typeof window.MobPageLoader?.show === 'function') {
            window.MobPageLoader.show();
            form.submit();
        } else {
            form.submit();
        }
    });

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && !modal.hidden) {
            closeModal();
        }
    });

    window.MobDashConfirm = {
        bindForm,
        bindAll: bindAllConfirmForms,
        open: openModal,
        close: closeModal,
    };
})();
