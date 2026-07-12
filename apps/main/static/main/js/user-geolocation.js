(function () {
    const STORAGE_KEY = 'mob_user_coords';

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

    function errorMessage(error) {
        if (!error || error.code == null) {
            return 'Não foi possível obter a sua localização.';
        }
        switch (error.code) {
            case 1:
                return 'Permita o acesso à localização nas definições do browser.';
            case 2:
                return 'Não foi possível obter a localização atual.';
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

            navigator.geolocation.getCurrentPosition(
                (position) => {
                    const coords = {
                        lat: position.coords.latitude,
                        lng: position.coords.longitude,
                        accuracy: position.coords.accuracy,
                    };
                    save(coords);
                    resolve(coords);
                },
                (error) => reject({ code: error.code, message: errorMessage(error) }),
                {
                    enableHighAccuracy: true,
                    timeout: 15000,
                    maximumAge: 0,
                    ...options,
                }
            );
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
