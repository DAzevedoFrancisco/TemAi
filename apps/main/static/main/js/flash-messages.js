(function () {
    const DURATION = {
        success: 4000,
        info: 5000,
        warning: 5500,
        error: 6000,
        default: 5000,
    };

    function getDuration(messageEl) {
        const classList = messageEl.classList;

        if (classList.contains('client-message-success') || classList.contains('success')) {
            return DURATION.success;
        }
        if (classList.contains('client-message-info') || classList.contains('info')) {
            return DURATION.info;
        }
        if (classList.contains('client-message-warning') || classList.contains('warning')) {
            return DURATION.warning;
        }
        if (classList.contains('client-message-error') || classList.contains('error')) {
            return DURATION.error;
        }
        return DURATION.default;
    }

    function dismissMessage(messageEl) {
        if (!messageEl || messageEl.classList.contains('is-dismissing')) {
            return;
        }

        let removed = false;
        messageEl.classList.add('is-dismissing');

        const removeMessage = () => {
            if (removed) {
                return;
            }
            removed = true;

            const container = messageEl.closest('.client-messages, .dash-messages, .home-flash-messages');
            const flashWrap = messageEl.closest('.home-flash-wrap');
            messageEl.remove();

            if (container && !container.querySelector('.client-message, .dash-message')) {
                container.remove();
            }
            if (flashWrap && !flashWrap.querySelector('.client-message')) {
                flashWrap.remove();
            }
        };

        const fallbackTimer = window.setTimeout(removeMessage, 500);
        messageEl.addEventListener('transitionend', () => {
            window.clearTimeout(fallbackTimer);
            removeMessage();
        }, { once: true });
    }

    function initFlashMessages(root) {
        const scope = root || document;
        scope.querySelectorAll('.client-message, .dash-message').forEach((messageEl) => {
            window.setTimeout(() => dismissMessage(messageEl), getDuration(messageEl));
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => initFlashMessages());
    } else {
        initFlashMessages();
    }

    window.MobFlashMessages = { initFlashMessages, dismissMessage };
})();
