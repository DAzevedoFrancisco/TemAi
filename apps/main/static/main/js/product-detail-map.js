(function () {
    /* Mesmos limites de apps/vendor/geo.py */
    const BEIRA_BOUNDS = {
        latMin: -19.902,
        latMax: -19.768,
        lngMin: 34.802,
        lngMax: 34.928,
    };

    function beiraLatLngBounds() {
        return L.latLngBounds(
            [BEIRA_BOUNDS.latMin, BEIRA_BOUNDS.lngMin],
            [BEIRA_BOUNDS.latMax, BEIRA_BOUNDS.lngMax]
        );
    }

    function isWithinBeira(lat, lng) {
        return (
            lat >= BEIRA_BOUNDS.latMin
            && lat <= BEIRA_BOUNDS.latMax
            && lng >= BEIRA_BOUNDS.lngMin
            && lng <= BEIRA_BOUNDS.lngMax
        );
    }

    function limitMapToBeira(map) {
        const bounds = beiraLatLngBounds();
        map.setMaxBounds(bounds.pad(0.02));
        map.options.maxBoundsViscosity = 1.0;
        map.setMinZoom(12);
    }

    function createStoreIcon() {
        return L.divIcon({
            className: 'product-map-marker product-map-marker-store',
            html: '<span>Loja</span>',
            iconSize: [52, 28],
            iconAnchor: [26, 14],
        });
    }

    function readConfig() {
        const dataEl = document.getElementById('product-map-data');
        if (!dataEl) {
            return null;
        }
        try {
            const data = JSON.parse(dataEl.textContent);
            const lat = Number(data.lat);
            const lng = Number(data.lng);
            if (!Number.isFinite(lat) || !Number.isFinite(lng)) {
                return null;
            }
            return {
                lat,
                lng,
                name: data.name || '',
            };
        } catch (_error) {
            return null;
        }
    }

    function hasLoadedTiles(mapEl) {
        return Boolean(mapEl.querySelector('.leaflet-tile-loaded'));
    }

    function bootProductDetailMap() {
        const mapEl = document.getElementById('product-map');
        if (!mapEl || typeof MobLocationMap === 'undefined' || typeof L === 'undefined') {
            return false;
        }

        if (mapEl.dataset.mapReady === 'true' && hasLoadedTiles(mapEl)) {
            return true;
        }

        const config = readConfig();
        if (!config) {
            return false;
        }

        if (mapEl.offsetHeight < 120) {
            mapEl.style.minHeight = '240px';
        }

        const storeInBeira = isWithinBeira(config.lat, config.lng);
        const markers = storeInBeira
            ? [{
                lat: config.lat,
                lng: config.lng,
                icon: createStoreIcon(),
                popup: config.name,
            }]
            : [];

        const map = MobLocationMap.init('product-map', {
            markers,
            defaultZoom: 15,
            openFirstPopup: false,
        });

        if (!map) {
            return false;
        }

        limitMapToBeira(map);

        if (storeInBeira) {
            map.setView([config.lat, config.lng], 15);
        } else {
            map.fitBounds(beiraLatLngBounds(), { padding: [18, 18], maxZoom: 14 });
        }

        mapEl.dataset.mapReady = 'true';

        const refresh = () => map.invalidateSize({ animate: false });
        refresh();
        [100, 300, 600, 1200, 2000].forEach((delay) => {
            window.setTimeout(refresh, delay);
        });

        if (typeof MobUserGeolocation !== 'undefined' && mapEl.dataset.userGeoAttached !== 'true') {
            mapEl.dataset.userGeoAttached = 'true';

            const params = new URLSearchParams(window.location.search);
            const lat = Number(params.get('lat'));
            const lng = Number(params.get('lng'));
            const knownPosition = Number.isFinite(lat) && Number.isFinite(lng) && isWithinBeira(lat, lng)
                ? { lat, lng }
                : null;

            MobUserGeolocation.attachToMap(map, mapEl, {
                position: knownPosition,
                quiet: Boolean(knownPosition),
                skipFitBounds: true,
            }).then((result) => {
                if (!result || !result.position) {
                    return;
                }
                if (!isWithinBeira(result.position.lat, result.position.lng)) {
                    if (result.marker) {
                        map.removeLayer(result.marker);
                    }
                }
            });
        }

        window.setTimeout(() => {
            if (!hasLoadedTiles(mapEl)) {
                mapEl.dataset.mapReady = 'false';
                mapEl.dataset.userGeoAttached = 'false';
                bootProductDetailMap();
            }
        }, 2800);

        return true;
    }

    function start() {
        if (bootProductDetailMap()) {
            return;
        }
        window.setTimeout(bootProductDetailMap, 350);
        window.setTimeout(bootProductDetailMap, 1000);
        window.setTimeout(bootProductDetailMap, 2000);
    }

    const mapEl = document.getElementById('product-map');
    if (!mapEl) {
        return;
    }

    if ('IntersectionObserver' in window) {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach((entry) => {
                if (entry.isIntersecting) {
                    start();
                }
            });
        }, { threshold: 0.01, rootMargin: '160px 0px' });
        observer.observe(mapEl);
    }

    if (document.readyState === 'complete') {
        start();
    } else {
        window.addEventListener('load', start, { once: true });
    }
})();
