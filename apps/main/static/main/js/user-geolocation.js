(function () {
    function createUserIcon(label) {
        return L.divIcon({
            className: 'product-map-marker product-map-marker-user',
            html: `<span>${label || 'Você'}</span>`,
            iconSize: [56, 28],
            iconAnchor: [28, 14],
        });
    }

    function requestPosition(options = {}) {
        return new Promise((resolve, reject) => {
            if (!navigator.geolocation) {
                reject({ code: 0, message: 'Geolocalização não suportada.' });
                return;
            }

            navigator.geolocation.getCurrentPosition(
                (position) => {
                    resolve({
                        lat: position.coords.latitude,
                        lng: position.coords.longitude,
                        accuracy: position.coords.accuracy,
                    });
                },
                (error) => reject(error),
                {
                    enableHighAccuracy: options.enableHighAccuracy !== false,
                    timeout: options.timeout || 12000,
                    maximumAge: options.maximumAge || 60000,
                }
            );
        });
    }

    function setStatus(mapEl, message, type) {
        if (!mapEl) {
            return;
        }

        let statusEl = mapEl.parentElement?.querySelector('.map-geo-status');
        if (!message) {
            if (statusEl) {
                statusEl.hidden = true;
                statusEl.textContent = '';
            }
            return;
        }

        if (!statusEl) {
            statusEl = document.createElement('p');
            statusEl.className = 'map-geo-status';
            statusEl.setAttribute('role', 'status');
            mapEl.insertAdjacentElement('afterend', statusEl);
        }

        statusEl.hidden = false;
        statusEl.textContent = message;
        statusEl.className = `map-geo-status map-geo-status--${type || 'info'}`;
    }

    function errorMessage(error) {
        if (!error || typeof error.code === 'undefined') {
            return 'Não foi possível obter a sua localização.';
        }

        switch (error.code) {
            case error.PERMISSION_DENIED:
                return 'Permissão de localização recusada. Active o GPS no navegador para ver a sua posição.';
            case error.POSITION_UNAVAILABLE:
                return 'Localização indisponível no momento.';
            case error.TIMEOUT:
                return 'A localização demorou demasiado. Tente novamente.';
            default:
                return 'Não foi possível obter a sua localização.';
        }
    }

    /**
     * Pede a posição via navigator.geolocation e marca "Você" no mapa.
     * Não altera a lógica de negócios — só visualização.
     */
    function attachToMap(map, mapEl, options = {}) {
        if (!map || typeof L === 'undefined') {
            return Promise.resolve(null);
        }

        setStatus(mapEl, 'A obter a sua localização...', 'info');

        return requestPosition(options)
            .then((position) => {
                const userMarker = L.marker(
                    [position.lat, position.lng],
                    { icon: createUserIcon(options.label || 'Você') }
                ).addTo(map);

                userMarker.bindPopup(options.popup || 'A sua localização');

                const layers = [];
                map.eachLayer((layer) => {
                    if (layer instanceof L.Marker) {
                        layers.push(layer);
                    }
                });

                if (layers.length > 1) {
                    map.fitBounds(L.featureGroup(layers).getBounds().pad(options.fitPadding || 0.25));
                } else {
                    map.setView([position.lat, position.lng], options.userZoom || 15);
                }

                setStatus(mapEl, 'Localização actual marcada no mapa.', 'success');
                window.setTimeout(() => setStatus(mapEl, ''), 3500);

                return { marker: userMarker, position };
            })
            .catch((error) => {
                setStatus(mapEl, errorMessage(error), 'warning');
                return null;
            });
    }

    window.MobUserGeolocation = {
        createUserIcon,
        requestPosition,
        attachToMap,
        setStatus,
    };
})();
