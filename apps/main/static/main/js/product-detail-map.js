(function () {
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

        const map = MobLocationMap.init('product-map', {
            markers: [{
                lat: config.lat,
                lng: config.lng,
                icon: createStoreIcon(),
                popup: config.name,
            }],
            defaultZoom: 15,
            openFirstPopup: false,
        });

        if (!map) {
            return false;
        }

        mapEl.dataset.mapReady = 'true';

        const refresh = () => map.invalidateSize({ animate: false });
        refresh();
        [100, 300, 600, 1200, 2000].forEach((delay) => {
            window.setTimeout(refresh, delay);
        });

        if (typeof MobUserGeolocation !== 'undefined' && mapEl.dataset.userGeoAttached !== 'true') {
            mapEl.dataset.userGeoAttached = 'true';
            MobUserGeolocation.attachToMap(map, mapEl);
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
