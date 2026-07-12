(function () {
    const eyeOpen = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>';
    const eyeClosed = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/></svg>';

    function setPasswordVisible(input, button, visible) {
        input.type = visible ? 'text' : 'password';
        button.setAttribute('aria-pressed', visible ? 'true' : 'false');
        button.setAttribute('aria-label', visible ? 'Ocultar senha' : 'Mostrar senha');
        button.setAttribute('title', visible ? 'Ocultar senha' : 'Mostrar senha');
        button.innerHTML = visible ? eyeClosed : eyeOpen;
    }

    document.querySelectorAll('.input-wrap-password input').forEach((input) => {
        const wrap = input.closest('.input-wrap-password');
        if (!wrap || wrap.querySelector('.password-toggle-btn')) {
            return;
        }

        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'password-toggle-btn';
        button.setAttribute('aria-pressed', 'false');
        button.setAttribute('aria-label', 'Mostrar senha');
        button.setAttribute('title', 'Mostrar senha');
        button.innerHTML = eyeOpen;

        button.addEventListener('click', () => {
            const visible = input.type === 'password';
            setPasswordVisible(input, button, visible);
        });

        wrap.appendChild(button);
    });
})();
