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

    function escapeHtml(value) {
        return String(value ?? '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function storeIcon() {
        return L.divIcon({
            className: 'product-map-marker product-map-marker-store',
            html: '<span>Loja</span>',
            iconSize: [52, 28],
            iconAnchor: [26, 14],
        });
    }

    function buildPopup(store) {
        const productsHtml = (store.products || []).map((product) => {
            const badge = product.available
                ? '<span class="search-map-popup-badge is-available">Disponível</span>'
                : '<span class="search-map-popup-badge is-unavailable">Indisponível</span>';
            return (
                `<a class="search-map-popup-product" href="${escapeHtml(product.url)}">`
                + `<strong>${escapeHtml(product.name)}</strong>`
                + badge
                + '</a>'
            );
        }).join('');

        return (
            `<div class="search-map-popup">`
            + `<strong class="search-map-popup-store">${escapeHtml(store.name)}</strong>`
            + (store.distance_label
                ? `<span class="search-map-popup-distance">${escapeHtml(store.distance_label)}</span>`
                : '')
            + (store.address
                ? `<span class="search-map-popup-address">${escapeHtml(store.address)}</span>`
                : '')
            + `<div class="search-map-popup-products">${productsHtml}</div>`
            + `</div>`
        );
    }

    function limitMapToBeira(map) {
        const bounds = beiraLatLngBounds();
        map.setMaxBounds(bounds.pad(0.02));
        map.options.maxBoundsViscosity = 1.0;
        map.setMinZoom(12);
        map.fitBounds(bounds, { padding: [18, 18], maxZoom: 14 });
    }

    function bootSearchResultsMap() {
        const mapEl = document.getElementById('search-results-map');
        const dataEl = document.getElementById('search-map-markers-data');
        if (!mapEl || !dataEl || typeof MobLocationMap === 'undefined' || typeof L === 'undefined') {
            return false;
        }

        let stores = [];
        try {
            stores = JSON.parse(dataEl.textContent);
        } catch (_error) {
            return false;
        }

        if (!Array.isArray(stores) || !stores.length) {
            return false;
        }

        const markers = stores
            .filter((store) => (
                Number.isFinite(store.lat)
                && Number.isFinite(store.lng)
                && isWithinBeira(store.lat, store.lng)
            ))
            .map((store) => ({
                lat: store.lat,
                lng: store.lng,
                icon: storeIcon(),
                popup: buildPopup(store),
            }));

        if (!markers.length) {
            return false;
        }

        const map = MobLocationMap.init('search-results-map', {
            markers,
            defaultZoom: 13,
            openFirstPopup: false,
            fitPadding: 0.2,
        });

        if (!map) {
            return false;
        }

        limitMapToBeira(map);
        mapEl.dataset.mapReady = 'true';

        if (typeof MobUserGeolocation !== 'undefined') {
            const params = new URLSearchParams(window.location.search);
            const lat = Number(params.get('lat'));
            const lng = Number(params.get('lng'));
            const knownPosition = Number.isFinite(lat) && Number.isFinite(lng) && isWithinBeira(lat, lng)
                ? { lat, lng }
                : null;

            MobUserGeolocation.attachToMap(map, mapEl, {
                fitPadding: 0.2,
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
                    return;
                }
                map.panTo([result.position.lat, result.position.lng], { animate: true });
            });
        }

        return true;
    }

    function start() {
        if (bootSearchResultsMap()) {
            return;
        }
        window.setTimeout(bootSearchResultsMap, 350);
        window.setTimeout(bootSearchResultsMap, 1000);
    }

    if (document.readyState === 'complete') {
        start();
    } else {
        window.addEventListener('load', start, { once: true });
    }
})();
