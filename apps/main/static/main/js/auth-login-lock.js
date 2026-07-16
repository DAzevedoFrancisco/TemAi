(function () {
    const form = document.getElementById('login-form');
    const submitBtn = document.getElementById('login-submit');
    if (!form || !submitBtn) {
        return;
    }

    const countdownEl = document.getElementById('login-lockout-countdown');
    const errorAlert = form.querySelector('.form-alert.error');
    const lockoutNotice = document.getElementById('login-lockout-notice');
    const lockoutPattern = /Excedeu o limite de \d+ tentativas/i;

    let locked = form.dataset.locked === 'true'
        || Boolean(lockoutNotice)
        || (errorAlert && lockoutPattern.test(errorAlert.textContent || ''));
    let seconds = parseInt(form.dataset.lockoutSeconds || '0', 10);
    let timerId = null;

    function setLockedState(isLocked) {
        locked = isLocked;
        submitBtn.disabled = isLocked;
        submitBtn.setAttribute('aria-disabled', isLocked ? 'true' : 'false');
        form.dataset.locked = isLocked ? 'true' : 'false';
        if (isLocked) {
            form.setAttribute('aria-disabled', 'true');
        } else {
            form.removeAttribute('aria-disabled');
        }
    }

    function preventSubmit(event) {
        if (!locked) {
            return;
        }
        event.preventDefault();
        event.stopImmediatePropagation();
    }

    form.addEventListener('submit', preventSubmit, true);
    submitBtn.addEventListener('click', function (event) {
        if (locked) {
            event.preventDefault();
            event.stopImmediatePropagation();
        }
    }, true);

    function tick() {
        if (seconds <= 0) {
            window.clearInterval(timerId);
            setLockedState(false);
            if (lockoutNotice) {
                lockoutNotice.remove();
            }
            return;
        }
        seconds -= 1;
        if (countdownEl) {
            countdownEl.textContent = String(seconds);
        }
    }

    if (locked) {
        setLockedState(true);
        if (seconds > 0) {
            timerId = window.setInterval(tick, 1000);
        }
    }
})();
