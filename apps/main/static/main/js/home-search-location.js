(function () {
    const form = document.querySelector('.search-form');
    const latInput = document.getElementById('search-lat');
    const lngInput = document.getElementById('search-lng');

    if (!form || !latInput || !lngInput) {
        return;
    }

    function applyCoords(coords) {
        latInput.value = coords.lat.toFixed(6);
        lngInput.value = coords.lng.toFixed(6);
    }

    form.addEventListener('submit', async (event) => {
        const queryInput = form.querySelector('input[name="q"]');
        if (!queryInput || !queryInput.value.trim()) {
            event.preventDefault();
            queryInput?.focus();
            return;
        }

        if (!navigator.geolocation) {
            return;
        }

        event.preventDefault();
        try {
            const coords = await MobGeolocation.request({ maximumAge: 0 });
            applyCoords(coords);
        } catch (error) {
            latInput.value = '';
            lngInput.value = '';
            if (error && error.message) {
                console.warn(error.message);
            }
        }

        if (!queryInput.value.trim()) {
            return;
        }
        form.submit();
    });
})();
