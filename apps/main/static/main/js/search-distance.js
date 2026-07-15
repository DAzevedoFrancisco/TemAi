(function () {
    if (typeof MobUserGeolocation === 'undefined') {
        return;
    }

    function withCoords(url, position) {
        const next = new URL(url, window.location.origin);
        next.searchParams.set('lat', position.lat.toFixed(6));
        next.searchParams.set('lng', position.lng.toFixed(6));
        return `${next.pathname}?${next.searchParams.toString()}`;
    }

    function hasCoords(params) {
        return Boolean(params.get('lat') && params.get('lng'));
    }

    function enrichSearchForms() {
        document.querySelectorAll('.search-form, .navbar-search-form').forEach((form) => {
            if (form.dataset.geoReady === 'true') {
                return;
            }
            form.dataset.geoReady = 'true';

            form.addEventListener('submit', (event) => {
                const action = new URL(form.action || window.location.href, window.location.origin);
                const formParams = new URLSearchParams(new FormData(form));
                if (hasCoords(action.searchParams) || hasCoords(formParams)) {
                    return;
                }

                const cached = MobUserGeolocation.getCachedPosition();
                if (!cached) {
                    return;
                }

                event.preventDefault();
                formParams.set('lat', cached.lat.toFixed(6));
                formParams.set('lng', cached.lng.toFixed(6));
                window.location.assign(`${action.pathname}?${formParams.toString()}`);
            });
        });
    }

    function resolveResultsPage() {
        const params = new URLSearchParams(window.location.search);
        const query = (params.get('q') || '').trim();
        const hint = document.getElementById('search-geo-hint');

        if (!query || hasCoords(params)) {
            return;
        }

        const cached = MobUserGeolocation.getCachedPosition();
        if (cached) {
            window.location.replace(withCoords(window.location.href, cached));
            return;
        }

        if (hint) {
            hint.hidden = false;
        }

        MobUserGeolocation.requestPosition()
            .then((position) => {
                window.location.replace(withCoords(window.location.href, position));
            })
            .catch(() => {
                if (hint) {
                    hint.textContent = 'Sem localização: resultados sem distância.';
                    hint.classList.add('search-distance-hint--warning');
                }
            });
    }

    enrichSearchForms();
    resolveResultsPage();

    /* Pré-aquece a localização em background para a 1.ª pesquisa ser mais rápida. */
    if (!MobUserGeolocation.getCachedPosition()) {
        MobUserGeolocation.requestPosition().catch(() => {});
    }
})();
