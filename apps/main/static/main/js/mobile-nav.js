(function () {
    const menu = document.getElementById('menu');
    const toggle = document.getElementById('menu-toggle');
    const backdrop = document.getElementById('mobile-nav-backdrop');

    if (!menu || !toggle) {
        return;
    }

    function setMenuOpen(isOpen) {
        menu.classList.toggle('active', isOpen);
        toggle.classList.toggle('is-open', isOpen);
        toggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
        toggle.setAttribute('aria-label', isOpen ? 'Fechar menu' : 'Abrir menu');

        if (backdrop) {
            backdrop.classList.toggle('is-visible', isOpen);
            backdrop.hidden = !isOpen;
            backdrop.setAttribute('aria-hidden', isOpen ? 'false' : 'true');
        }

        document.body.classList.toggle('mobile-nav-open', isOpen);
    }

    toggle.addEventListener('click', () => {
        setMenuOpen(!menu.classList.contains('active'));
    });

    if (backdrop) {
        backdrop.addEventListener('click', () => setMenuOpen(false));
    }

    menu.querySelectorAll('a, button.vendor-link, button.client-sidebar-logout').forEach((element) => {
        element.addEventListener('click', () => setMenuOpen(false));
    });

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && menu.classList.contains('active')) {
            setMenuOpen(false);
        }
    });
})();
