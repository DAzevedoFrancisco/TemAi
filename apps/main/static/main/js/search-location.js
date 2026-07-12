(function () {
    const locateBtn = document.getElementById('search-use-location');
    const refreshBtn = document.getElementById('search-refresh-location');

    const locateBtnDefaultHtml = locateBtn ? locateBtn.innerHTML : '';
    const refreshBtnDefaultHtml = refreshBtn ? refreshBtn.innerHTML : '';

    async function applyFreshLocation(button, defaultHtml) {
        if (!button) {
            return;
        }

        button.disabled = true;
        const label = button.querySelector('.search-location-btn-label');
        if (label) {
            label.textContent = 'A obter localização...';
        } else {
            button.textContent = 'A obter localização...';
        }

        try {
            const coords = await MobGeolocation.request({ maximumAge: 0 });
            window.location.search = MobGeolocation.appendToUrl(coords).toString();
        } catch (error) {
            button.disabled = false;
            button.innerHTML = defaultHtml;
            alert(error.message || MobGeolocation.errorMessage(error));
        }
    }

    if (locateBtn && navigator.geolocation) {
        locateBtn.addEventListener('click', () => applyFreshLocation(locateBtn, locateBtnDefaultHtml));
    }

    if (refreshBtn && navigator.geolocation) {
        refreshBtn.addEventListener('click', () => applyFreshLocation(refreshBtn, refreshBtnDefaultHtml));
    }
})();
