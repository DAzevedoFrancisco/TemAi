(function () {
    const statusEl = document.getElementById('become-seller-geo-status');
    const form = document.getElementById('become-seller-form');
    const submitBtn = document.getElementById('become-seller-submit');
    const cancelLink = document.getElementById('become-seller-cancel');
    const latInput = document.getElementById('become-seller-lat');
    const lngInput = document.getElementById('become-seller-lng');

    if (!statusEl || !form || typeof MobUserGeolocation === 'undefined') {
        return;
    }

    // Limites da Beira (mesmos do backend apps/vendor/geo.py)
    const BEIRA_BOUNDS = {
        latMin: -19.902,
        latMax: -19.768,
        lngMin: 34.802,
        lngMax: 34.928,
    };

    function isWithinBeira(lat, lng) {
        return (
            lat >= BEIRA_BOUNDS.latMin
            && lat <= BEIRA_BOUNDS.latMax
            && lng >= BEIRA_BOUNDS.lngMin
            && lng <= BEIRA_BOUNDS.lngMax
        );
    }

    function setBlocked(message) {
        statusEl.textContent = message;
        statusEl.className = 'become-seller-geo-status become-seller-geo-status--blocked';
        form.hidden = true;
        if (cancelLink) {
            cancelLink.hidden = false;
        }
    }

    function setReady() {
        statusEl.textContent = 'Localização confirmada na Beira. Pode continuar.';
        statusEl.className = 'become-seller-geo-status become-seller-geo-status--ok';
        form.hidden = false;
        if (submitBtn) {
            submitBtn.disabled = false;
        }
        if (cancelLink) {
            cancelLink.hidden = true;
        }
    }

    MobUserGeolocation.requestPosition()
        .then((position) => {
            if (!isWithinBeira(position.lat, position.lng)) {
                setBlocked(
                    'A sua localização actual está fora da cidade da Beira. '
                    + 'Só pode tornar-se vendedor estando na Beira.'
                );
                return;
            }

            latInput.value = position.lat.toFixed(6);
            lngInput.value = position.lng.toFixed(6);
            setReady();
        })
        .catch((error) => {
            let message = 'Não foi possível obter a sua localização. Active o GPS e autorize o acesso para se tornar vendedor.';
            if (error && error.code === 1) {
                message = 'Localização recusada. Sem autorização do GPS não pode tornar-se vendedor.';
            } else if (error && error.code === 0) {
                message = 'Este dispositivo ou navegador não suporta geolocalização. Não pode tornar-se vendedor.';
            }
            setBlocked(message);
        });
})();
