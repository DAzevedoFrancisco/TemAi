(function () {
    const params = new URLSearchParams(window.location.search);
    const query = (params.get('q') || '').trim();
    const hasCoords = params.get('lat') && params.get('lng');
    const hint = document.getElementById('search-geo-hint');

    if (!query || hasCoords || typeof MobUserGeolocation === 'undefined') {
        return;
    }

    if (hint) {
        hint.hidden = false;
    }

    MobUserGeolocation.requestPosition()
        .then((position) => {
            params.set('lat', position.lat.toFixed(6));
            params.set('lng', position.lng.toFixed(6));
            const nextUrl = `${window.location.pathname}?${params.toString()}`;
            window.location.replace(nextUrl);
        })
        .catch(() => {
            if (hint) {
                hint.textContent = 'Sem localização: resultados sem ordenação por distância.';
                hint.classList.add('search-distance-hint--warning');
            }
        });
})();
