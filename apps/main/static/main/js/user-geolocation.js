(function () {
    const STORAGE_KEY = 'mob_user_coords';
    const BEIRA_CENTER = { lat: -19.8436, lng: 34.8389 };
    const CENTER_FALLBACK_RADIUS_KM = 0.2;
    const MIN_ACCURACY_FOR_CENTER_KM = 1500;

    function save(coords) {
        try {
            sessionStorage.setItem(STORAGE_KEY, JSON.stringify({
                lat: coords.lat,
                lng: coords.lng,
                accuracy: coords.accuracy ?? null,
                ts: Date.now(),
            }));
        } catch (_) {
            /* ignore storage errors */
        }
    }

    function load(maxAgeMs = 0) {
        if (!maxAgeMs) {
            return null;
        }
        try {
            const raw = sessionStorage.getItem(STORAGE_KEY);
            if (!raw) {
                return null;
            }
            const data = JSON.parse(raw);
            if (data.lat == null || data.lng == null) {
                return null;
            }
            if (Date.now() - data.ts > maxAgeMs) {
                return null;
            }
            return { lat: data.lat, lng: data.lng, accuracy: data.accuracy ?? null };
        } catch (_) {
            return null;
        }
    }

    function haversineKm(lat1, lon1, lat2, lon2) {
        const earthRadiusKm = 6371;
        const phi1 = lat1 * Math.PI / 180;
        const phi2 = lat2 * Math.PI / 180;
        const deltaPhi = (lat2 - lat1) * Math.PI / 180;
        const deltaLambda = (lon2 - lon1) * Math.PI / 180;
        const a = Math.sin(deltaPhi / 2) ** 2
            + Math.cos(phi1) * Math.cos(phi2) * Math.sin(deltaLambda / 2) ** 2;
        return earthRadiusKm * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    }

    function isLikelyCityCenterFallback(coords) {
        if (coords.accuracy == null || coords.accuracy < MIN_ACCURACY_FOR_CENTER_KM) {
            return false;
        }
        return haversineKm(
            coords.lat,
            coords.lng,
            BEIRA_CENTER.lat,
            BEIRA_CENTER.lng
        ) <= CENTER_FALLBACK_RADIUS_KM;
    }

    function normalizeCoords(position) {
        return {
            lat: position.coords.latitude,
            lng: position.coords.longitude,
            accuracy: position.coords.accuracy,
        };
    }

    function errorMessage(error) {
        if (!error || error.code == null) {
            return 'Não foi possível obter a sua localização.';
        }
        switch (error.code) {
            case 1:
                return 'Permita o acesso à localização nas definições do browser.';
            case 2:
                return error.message || 'Não foi possível obter a localização atual.';
            case 3:
                return 'A deteção da localização demorou demasiado. Tente novamente.';
            default:
                return 'Não foi possível obter a sua localização.';
        }
    }

    function request(options = {}) {
        return new Promise((resolve, reject) => {
            if (!navigator.geolocation) {
                reject({ code: 0, message: 'O seu browser não suporta geolocalização.' });
                return;
            }

            const geoOptions = {
                enableHighAccuracy: true,
                timeout: 15000,
                maximumAge: 0,
                ...options,
            };
            const targetAccuracy = options.targetAccuracy ?? 120;
            const watchTimeoutMs = options.watchTimeoutMs ?? 12000;
            let watchId = null;
            let bestPosition = null;
            let settled = false;

            function cleanup() {
                if (watchId != null) {
                    navigator.geolocation.clearWatch(watchId);
                    watchId = null;
                }
            }

            function settle(position) {
                if (settled) {
                    return;
                }
                settled = true;
                cleanup();
                clearTimeout(fallbackTimer);

                const coords = normalizeCoords(position);
                if (isLikelyCityCenterFallback(coords)) {
                    reject({
                        code: 2,
                        message: 'A localização obtida é imprecisa (estimativa por rede). Active o GPS do dispositivo ou tente novamente ao ar livre.',
                    });
                    return;
                }

                save(coords);
                resolve(coords);
            }

            function fail(error) {
                if (settled) {
                    return;
                }
                settled = true;
                cleanup();
                clearTimeout(fallbackTimer);
                reject({ code: error.code, message: errorMessage(error) });
            }

            watchId = navigator.geolocation.watchPosition(
                (position) => {
                    if (!bestPosition || position.coords.accuracy < bestPosition.coords.accuracy) {
                        bestPosition = position;
                    }
                    if (position.coords.accuracy <= targetAccuracy) {
                        settle(position);
                    }
                },
                fail,
                geoOptions
            );

            const fallbackTimer = setTimeout(() => {
                if (settled) {
                    return;
                }
                if (bestPosition) {
                    settle(bestPosition);
                    return;
                }
                navigator.geolocation.getCurrentPosition(settle, fail, geoOptions);
            }, watchTimeoutMs);
        });
    }

    function appendToUrl(coords, baseSearch) {
        const params = new URLSearchParams(baseSearch || window.location.search);
        params.set('lat', coords.lat.toFixed(6));
        params.set('lng', coords.lng.toFixed(6));
        return params;
    }

    window.MobGeolocation = {
        STORAGE_KEY,
        save,
        load,
        request,
        errorMessage,
        appendToUrl,
    };
})();
