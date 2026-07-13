(function () {
    function destroyMap(container) {
        if (container && container._mobMap) {
            container._mobMap.remove();
            container._mobMap = null;
        }
    }

    function init(containerId, options = {}) {
        const container = document.getElementById(containerId);
        if (!container || typeof L === 'undefined' || !window.MobMapTiles) {
            return null;
        }

        const {
            markers = [],
            fitPadding = 0.2,
            defaultZoom = 15,
            openFirstPopup = true,
            preferCanvas = false,
        } = options;

        const containerRect = container.getBoundingClientRect();
        if (containerRect.width < 1 || containerRect.height < 1) {
            return null;
        }

        destroyMap(container);

        const map = L.map(containerId, {
            scrollWheelZoom: false,
            preferCanvas,
        });
        const tileLayer = MobMapTiles.addTileLayer(map);
        container._mobMap = map;
        container._mobTileLayer = tileLayer;

        const allMarkers = [];

        markers.forEach((markerConfig) => {
            const marker = L.marker(
                [markerConfig.lat, markerConfig.lng],
                markerConfig.icon ? { icon: markerConfig.icon } : {}
            ).addTo(map);
            if (markerConfig.popup) {
                marker.bindPopup(markerConfig.popup);
            }
            allMarkers.push(marker);
        });

        if (allMarkers.length > 1) {
            map.fitBounds(L.featureGroup(allMarkers).getBounds().pad(fitPadding));
        } else if (allMarkers.length === 1) {
            const position = allMarkers[0].getLatLng();
            map.setView([position.lat, position.lng], defaultZoom);
            if (openFirstPopup && allMarkers[0].getPopup()) {
                allMarkers[0].openPopup();
            }
        }

        const refresh = () => map.invalidateSize({ animate: false });
        map.whenReady(refresh);
        requestAnimationFrame(refresh);
        [120, 350, 700, 1200, 2000].forEach((delay) => {
            window.setTimeout(refresh, delay);
        });
        window.addEventListener('resize', refresh);
        window.addEventListener('orientationchange', () => {
            window.setTimeout(refresh, 350);
        });

        if (typeof ResizeObserver !== 'undefined') {
            const resizeObserver = new ResizeObserver(refresh);
            resizeObserver.observe(container);
        }

        return map;
    }

    window.MobLocationMap = {
        init,
        destroyMap,
    };
})();
