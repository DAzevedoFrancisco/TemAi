(function () {
    const BEIRA_CENTER = { lat: -19.8436, lng: 34.8389 };
    const BEIRA_CENTER_RADIUS_KM = 0.2;

    function isMozambiqueLatitude(value) {
        return value >= -27 && value <= -10;
    }

    function isMozambiqueLongitude(value) {
        return value >= 30 && value <= 42;
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

    function fixSwappedCoordinates(latitude, longitude) {
        if (latitude == null || longitude == null) {
            return { lat: null, lng: null };
        }

        let lat = Number(latitude);
        let lng = Number(longitude);

        if (Number.isNaN(lat) || Number.isNaN(lng)) {
            return { lat: null, lng: null };
        }

        if (lat < -90 || lat > 90 || lng < -180 || lng > 180) {
            return { lat: null, lng: null };
        }

        if (isMozambiqueLongitude(lat) && isMozambiqueLatitude(lng)) {
            [lat, lng] = [lng, lat];
        } else if (Math.abs(lat) > Math.abs(lng) && Math.abs(lat) >= 30 && Math.abs(lng) <= 27) {
            [lat, lng] = [lng, lat];
        }

        return { lat, lng };
    }

    function isNearBeiraCenter(latitude, longitude, radiusKm = BEIRA_CENTER_RADIUS_KM) {
        if (latitude == null || longitude == null) {
            return false;
        }
        return haversineKm(
            Number(latitude),
            Number(longitude),
            BEIRA_CENTER.lat,
            BEIRA_CENTER.lng
        ) <= radiusKm;
    }

    window.MobCoordinates = {
        BEIRA_CENTER,
        fixSwappedCoordinates,
        isNearBeiraCenter,
    };
})();
