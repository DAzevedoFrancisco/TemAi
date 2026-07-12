(function () {
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

    function userIcon() {
        return L.divIcon({
            className: 'product-map-marker product-map-marker-user',
            html: '<span>Você</span>',
            iconSize: [52, 28],
            iconAnchor: [26, 14],
        });
    }

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
            userLat = null,
            userLng = null,
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

        let normalizedUserLat = userLat;
        let normalizedUserLng = userLng;
        if (normalizedUserLat != null && normalizedUserLng != null && window.MobCoordinates) {
            const normalized = MobCoordinates.fixSwappedCoordinates(normalizedUserLat, normalizedUserLng);
            normalizedUserLat = normalized.lat;
            normalizedUserLng = normalized.lng;
        }

        destroyMap(container);

        if (window.MobMapTiles && typeof MobMapTiles.applyLeafletReferrerPolicy === 'function') {
            MobMapTiles.applyLeafletReferrerPolicy();
        }

        const map = L.map(containerId, {
            scrollWheelZoom: false,
            preferCanvas,
        });
        L.tileLayer(MobMapTiles.url, MobMapTiles.options).addTo(map);
        container._mobMap = map;

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

        if (normalizedUserLat != null && normalizedUserLng != null) {
            const userMarker = L.marker([normalizedUserLat, normalizedUserLng], { icon: userIcon() })
                .addTo(map)
                .bindPopup('A sua localização');
            allMarkers.push(userMarker);
        }

        if (allMarkers.length > 1) {
            map.fitBounds(L.featureGroup(allMarkers).getBounds().pad(fitPadding));
        } else if (allMarkers.length === 1) {
            const position = allMarkers[0].getLatLng();
            map.setView([position.lat, position.lng], defaultZoom);
            if (openFirstPopup && allMarkers[0].getPopup()) {
                allMarkers[0].openPopup();
            }
        } else if (normalizedUserLat != null && normalizedUserLng != null) {
            map.setView([normalizedUserLat, normalizedUserLng], defaultZoom);
        }

        const refresh = () => map.invalidateSize({ animate: false });
        map.whenReady(refresh);
        requestAnimationFrame(refresh);
        setTimeout(refresh, 200);
        setTimeout(refresh, 600);
        window.addEventListener('resize', refresh);

        return map;
    }

    window.MobLocationMap = {
        haversineKm,
        init,
        destroyMap,
    };
})();
