(function () {
    function isMozambiqueLatitude(value) {
        return value >= -27 && value <= -10;
    }

    function isMozambiqueLongitude(value) {
        return value >= 30 && value <= 42;
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

    window.MobCoordinates = {
        fixSwappedCoordinates,
    };
})();
