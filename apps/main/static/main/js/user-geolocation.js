(function () {
    const CACHE_KEY = 'mob_user_geo_v1';
    const DEFAULT_OPTIONS = {
        enableHighAccuracy: true,
        timeout: 15000,
        maximumAge: 120000,
    };

    function createUserIcon(label) {
        return L.divIcon({
            className: 'product-map-marker product-map-marker-user',
            html: `<span>${label || 'Você'}</span>`,
            iconSize: [56, 28],
            iconAnchor: [28, 14],
        });
    }

    function getCachedPosition(maxAge = DEFAULT_OPTIONS.maximumAge) {
        try {
            const raw = sessionStorage.getItem(CACHE_KEY);
            if (!raw) {
                return null;
            }
            const data = JSON.parse(raw);
            if (!data || !Number.isFinite(data.lat) || !Number.isFinite(data.lng)) {
                return null;
            }
            if (typeof maxAge === 'number' && maxAge >= 0 && Date.now() - Number(data.ts || 0) > maxAge) {
                return null;
            }
            return {
                lat: data.lat,
                lng: data.lng,
                accuracy: data.accuracy,
                fromCache: true,
            };
        } catch (_error) {
            return null;
        }
    }

    function saveCachedPosition(position) {
        if (!position || !Number.isFinite(position.lat) || !Number.isFinite(position.lng)) {
            return;
        }
        try {
            sessionStorage.setItem(CACHE_KEY, JSON.stringify({
                lat: position.lat,
                lng: position.lng,
                accuracy: position.accuracy,
                ts: Date.now(),
            }));
        } catch (_error) {
            /* ignore quota / private mode */
        }
    }

    function requestPosition(options = {}) {
        const opts = { ...DEFAULT_OPTIONS, ...options };

        if (!options.forceFresh) {
            const cached = getCachedPosition(opts.maximumAge);
            if (cached) {
                return Promise.resolve(cached);
            }
        }

        return new Promise((resolve, reject) => {
            if (!navigator.geolocation) {
                reject({ code: 0, message: 'Geolocalização não suportada.' });
                return;
            }

            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const result = {
                        lat: position.coords.latitude,
                        lng: position.coords.longitude,
                        accuracy: position.coords.accuracy,
                        fromCache: false,
                    };
                    saveCachedPosition(result);
                    resolve(result);
                },
                (error) => reject(error),
                {
                    enableHighAccuracy: Boolean(opts.enableHighAccuracy),
                    timeout: opts.timeout,
                    maximumAge: opts.maximumAge,
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

    function placeUserOnMap(map, position, options = {}) {
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

        return userMarker;
    }

    /**
     * Marca "Você" no mapa. Usa posição já conhecida / cache antes de pedir GPS.
     */
    function attachToMap(map, mapEl, options = {}) {
        if (!map || typeof L === 'undefined') {
            return Promise.resolve(null);
        }

        const known = options.position
            && Number.isFinite(options.position.lat)
            && Number.isFinite(options.position.lng)
            ? options.position
            : getCachedPosition(options.maximumAge);

        if (known) {
            saveCachedPosition(known);
            const marker = placeUserOnMap(map, known, options);
            if (!options.quiet) {
                setStatus(mapEl, '');
            }
            return Promise.resolve({ marker, position: known });
        }

        if (!options.quiet) {
            setStatus(mapEl, 'A obter a sua localização...', 'info');
        }

        return requestPosition(options)
            .then((position) => {
                const marker = placeUserOnMap(map, position, options);
                if (!options.quiet) {
                    setStatus(mapEl, '');
                }
                return { marker, position };
            })
            .catch((error) => {
                if (!options.quiet) {
                    setStatus(mapEl, errorMessage(error), 'warning');
                }
                return null;
            });
    }

    window.MobUserGeolocation = {
        createUserIcon,
        requestPosition,
        getCachedPosition,
        saveCachedPosition,
        attachToMap,
        setStatus,
    };
})();
