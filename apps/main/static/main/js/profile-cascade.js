(function () {
    function closeCascade(root) {
        const toggle = root.querySelector('.profile-cascade-toggle');
        const panel = root.querySelector('.profile-cascade-panel');
        if (!toggle || !panel) {
            return;
        }
        toggle.setAttribute('aria-expanded', 'false');
        panel.hidden = true;
        root.classList.remove('is-open');
    }

    function openCascade(root) {
        const toggle = root.querySelector('.profile-cascade-toggle');
        const panel = root.querySelector('.profile-cascade-panel');
        if (!toggle || !panel) {
            return;
        }
        toggle.setAttribute('aria-expanded', 'true');
        panel.hidden = false;
        root.classList.add('is-open');
    }

    function bindCascade(root) {
        if (root.dataset.cascadeBound === 'true') {
            return;
        }
        root.dataset.cascadeBound = 'true';

        const toggle = root.querySelector('.profile-cascade-toggle');
        const panel = root.querySelector('.profile-cascade-panel');
        if (!toggle || !panel) {
            return;
        }

        toggle.addEventListener('click', (event) => {
            event.preventDefault();
            event.stopPropagation();
            const isOpen = toggle.getAttribute('aria-expanded') === 'true';
            if (isOpen) {
                closeCascade(root);
            } else {
                document.querySelectorAll('[data-profile-cascade].is-open').forEach((other) => {
                    if (other !== root) {
                        closeCascade(other);
                    }
                });
                openCascade(root);
            }
        });
    }

    document.querySelectorAll('[data-profile-cascade]').forEach(bindCascade);

    document.addEventListener('click', (event) => {
        document.querySelectorAll('[data-profile-cascade].is-open').forEach((root) => {
            if (!root.contains(event.target)) {
                closeCascade(root);
            }
        });
    });

    document.addEventListener('keydown', (event) => {
        if (event.key !== 'Escape') {
            return;
        }
        document.querySelectorAll('[data-profile-cascade].is-open').forEach(closeCascade);
    });
})();
