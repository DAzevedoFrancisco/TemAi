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

            // /#about (e âncoras na mesma página): o browser não recarrega —
            // se mostrarmos o loader, ele nunca esconde.
            if (isSameDocumentHashNavigation(url)) {
                return false;
            }

            return true;
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

    // Hide as soon as the document is interactive; do not wait for
    // fonts, images or map tiles (window.load).
    if (document.readyState === 'interactive' || document.readyState === 'complete') {
        hideLoader();
    } else {
        document.addEventListener('DOMContentLoaded', hideLoader, { once: true });
    }

    // Safety net if a late navigation interrupted hide timing.
    window.addEventListener('load', hideLoader, { once: true });
})();
