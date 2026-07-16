(function () {
    const LOADER_ID = 'mob-page-loader';
    const LOADING_CLASS = 'mob-page-loading';
    const ACTIVE_CLASS = 'is-active';
    const HIDING_CLASS = 'is-hiding';
    const MIN_VISIBLE_MS = 80;

    let shownAt = Date.now();
    let hideTimer = null;
    let hideScheduled = false;

    function getLoader() {
        return document.getElementById(LOADER_ID);
    }

    function setPageLoadingState(isLoading) {
        document.documentElement.classList.toggle(LOADING_CLASS, isLoading);
    }

    function showLoader() {
        const loader = getLoader();
        if (!loader) {
            return;
        }

        if (hideTimer) {
            window.clearTimeout(hideTimer);
            hideTimer = null;
        }
        hideScheduled = false;

        loader.classList.remove(HIDING_CLASS);
        loader.classList.add(ACTIVE_CLASS);
        loader.setAttribute('aria-hidden', 'false');
        setPageLoadingState(true);
        shownAt = Date.now();
    }

    function hideLoader() {
        const loader = getLoader();
        if (!loader || !loader.classList.contains(ACTIVE_CLASS)) {
            setPageLoadingState(false);
            return;
        }

        if (hideScheduled) {
            return;
        }
        hideScheduled = true;

        const elapsed = Date.now() - shownAt;
        const delay = Math.max(0, MIN_VISIBLE_MS - elapsed);

        hideTimer = window.setTimeout(function () {
            loader.classList.add(HIDING_CLASS);
            loader.classList.remove(ACTIVE_CLASS);
            loader.setAttribute('aria-hidden', 'true');
            setPageLoadingState(false);
            hideScheduled = false;

            window.setTimeout(function () {
                loader.classList.remove(HIDING_CLASS);
            }, 180);
        }, delay);
    }

    function isSameDocumentHashNavigation(url) {
        return (
            url.pathname === window.location.pathname
            && url.search === window.location.search
            && Boolean(url.hash)
        );
    }

    function isInternalNavigationLink(anchor) {
        if (!anchor || anchor.target === '_blank' || anchor.hasAttribute('download')) {
            return false;
        }

        const href = anchor.getAttribute('href');
        if (!href || href.startsWith('#') || href.startsWith('mailto:') || href.startsWith('tel:') || href.startsWith('javascript:')) {
            return false;
        }

        try {
            const url = new URL(anchor.href, window.location.href);
            if (url.origin !== window.location.origin) {
                return false;
            }

            if (isSameDocumentHashNavigation(url)) {
                return false;
            }

            return true;
        } catch (_error) {
            return false;
        }
    }

    function isModalOpen() {
        return Boolean(document.querySelector(
            '.dash-modal:not([hidden]), .logout-modal:not([hidden])'
        ));
    }

    function shouldShowForForm(form) {
        if (!form || !(form instanceof HTMLFormElement)) {
            return false;
        }

        if (form.target === '_blank' || form.dataset.noLoader === 'true') {
            return false;
        }

        // Confirmação modal: loader só depois de confirmar.
        if (
            form.hasAttribute('data-confirm-message')
            || form.hasAttribute('data-confirm-title')
            || form.id === 'dash-logout-form'
            || form.id === 'account-delete-form'
        ) {
            return false;
        }

        // Formulário dentro de modal ainda aberto.
        if (form.closest('.dash-modal, .logout-modal')) {
            return false;
        }

        const method = (form.method || 'get').toLowerCase();
        return method === 'get' || method === 'post';
    }

    function submitForm(form) {
        if (!form || !(form instanceof HTMLFormElement)) {
            return;
        }
        showLoader();
        // HTMLFormElement.submit() não dispara o evento "submit".
        form.submit();
    }

    document.addEventListener('click', function (event) {
        if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) {
            return;
        }

        const anchor = event.target.closest('a');
        if (!isInternalNavigationLink(anchor)) {
            return;
        }

        // Não cobrir modais abertos / acções só de UI.
        if (anchor.closest('.dash-modal, .logout-modal')) {
            return;
        }

        showLoader();
    });

    // Capture + microtask: espera outros handlers (ex.: confirm modal) fazerem preventDefault.
    document.addEventListener('submit', function (event) {
        const form = event.target;
        if (!(form instanceof HTMLFormElement)) {
            return;
        }

        queueMicrotask(function () {
            if (event.defaultPrevented || !shouldShowForForm(form)) {
                return;
            }
            showLoader();
        });
    }, true);

    window.addEventListener('pageshow', function (event) {
        if (event.persisted) {
            hideLoader();
        }
    });

    if (document.readyState === 'interactive' || document.readyState === 'complete') {
        hideLoader();
    } else {
        document.addEventListener('DOMContentLoaded', hideLoader, { once: true });
    }

    window.addEventListener('load', hideLoader, { once: true });

    // Se um modal abrir com loader activo por engano, esconder.
    document.addEventListener('click', function () {
        if (isModalOpen() && getLoader()?.classList.contains(ACTIVE_CLASS)) {
            const openConfirm = document.querySelector(
                '#dash-confirm-modal:not([hidden]), #admin-confirm-modal:not([hidden]), #dash-logout-modal:not([hidden]), #account-delete-modal:not([hidden])'
            );
            if (openConfirm) {
                hideLoader();
            }
        }
    }, true);

    window.MobPageLoader = {
        show: showLoader,
        hide: hideLoader,
        submitForm,
    };
})();
