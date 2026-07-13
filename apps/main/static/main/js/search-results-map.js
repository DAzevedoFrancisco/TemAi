(function () {
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
            + (store.address
                ? `<span class="search-map-popup-address">${escapeHtml(store.address)}</span>`
                : '')
            + `<div class="search-map-popup-products">${productsHtml}</div>`
            + `</div>`
        );
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
            .filter((store) => Number.isFinite(store.lat) && Number.isFinite(store.lng))
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
            defaultZoom: 14,
            openFirstPopup: false,
            fitPadding: 0.25,
        });

        if (!map) {
            return false;
        }

        mapEl.dataset.mapReady = 'true';
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
