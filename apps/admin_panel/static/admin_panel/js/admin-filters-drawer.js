(function () {
    document.querySelectorAll('.admin-filters-drawer').forEach((drawer) => {
        const toggle = drawer.querySelector('.admin-filters-toggle');
        if (!toggle) {
            return;
        }

        toggle.addEventListener('click', () => {
            const isOpen = drawer.classList.toggle('is-open');
            toggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
        });
    });
})();
