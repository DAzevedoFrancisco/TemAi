(function () {
    const LOADER_ID = 'mob-page-loader';
    const LOADING_CLASS = 'mob-page-loading';
    const ACTIVE_CLASS = 'is-active';
    const HIDING_CLASS = 'is-hiding';
    const MIN_VISIBLE_MS = 280;

    let shownAt = Date.now();
    let hideTimer = null;

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

        const elapsed = Date.now() - shownAt;
        const delay = Math.max(0, MIN_VISIBLE_MS - elapsed);

        hideTimer = window.setTimeout(function () {
            loader.classList.add(HIDING_CLASS);
            loader.classList.remove(ACTIVE_CLASS);
            loader.setAttribute('aria-hidden', 'true');
            setPageLoadingState(false);

            window.setTimeout(function () {
                loader.classList.remove(HIDING_CLASS);
            }, 220);
        }, delay);
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
            return url.origin === window.location.origin;
        } catch (_error) {
            return false;
        }
    }

    function shouldShowForForm(form) {
        if (!form || form.target === '_blank' || form.dataset.noLoader === 'true') {
            return false;
        }

        if (form.method && form.method.toLowerCase() === 'get') {
            return true;
        }

        return form.method === '' || form.method.toLowerCase() === 'post';
    }

    document.addEventListener('click', function (event) {
        if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) {
            return;
        }

        const anchor = event.target.closest('a');
        if (!isInternalNavigationLink(anchor)) {
            return;
        }

        showLoader();
    });

    document.addEventListener('submit', function (event) {
        if (event.defaultPrevented || !shouldShowForForm(event.target)) {
            return;
        }

        showLoader();
    }, true);

    window.addEventListener('pageshow', function (event) {
        if (event.persisted) {
            hideLoader();
        }
    });

    if (document.readyState === 'complete') {
        hideLoader();
    } else {
        window.addEventListener('load', hideLoader, { once: true });
    }
})();
