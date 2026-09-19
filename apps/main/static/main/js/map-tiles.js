(function () {
    // Carto primeiro: o tile.openstreetmap.org devolve "Access blocked" com frequência
    // no Firefox (Tracking Protection / referrer em HTTP local).
    const PROVIDERS = [
        {
            url: 'https://{s}.basemaps.cartocdn.com/ rastertiles/voyager/{z}/{x}/{y}.png?key=cb1_3ko9_1_9482ecc00a2e520779f11c61',
            options: {
                maxZoom: 20,
                subdomains: 'abcd',
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>',
                crossOrigin: true,
            },
        },
        {
            url: 'https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png',
            options: {
                maxZoom: 19,
                subdomains: 'abc',
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> HOT',
                crossOrigin: true,
            },
        },
        {
            url: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
            options: {
                maxZoom: 19,
                attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
                crossOrigin: true,
            },
        },
    ];

    function addTileLayer(map) {
        let providerIndex = 0;
        let activeLayer = null;
        let failedTiles = 0;
        let loadedTiles = 0;

        function mountLayer() {
            if (activeLayer) {
                map.removeLayer(activeLayer);
                activeLayer = null;
            }

            if (providerIndex >= PROVIDERS.length) {
                return null;
            }

            const provider = PROVIDERS[providerIndex];
            providerIndex += 1;
            failedTiles = 0;
            loadedTiles = 0;

            activeLayer = L.tileLayer(provider.url, provider.options);
            activeLayer.on('tileload', () => {
                loadedTiles += 1;
            });
            activeLayer.on('tileerror', () => {
                failedTiles += 1;
                if (loadedTiles === 0 && failedTiles >= 3 && providerIndex < PROVIDERS.length) {
                    mountLayer();
                }
            });
            activeLayer.addTo(map);
            return activeLayer;
        }

        mountLayer();
        return {
            hasLoadedTiles() {
                return loadedTiles > 0;
            },
        };
    }

    const DEFAULT_PROVIDER = PROVIDERS[0];

    window.MobMapTiles = {
        url: DEFAULT_PROVIDER.url,
        options: DEFAULT_PROVIDER.options,
        providers: PROVIDERS,
        addTileLayer,
    };
})();
