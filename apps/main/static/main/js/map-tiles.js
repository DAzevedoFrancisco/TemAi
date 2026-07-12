(function () {
    const REFERRER_POLICY = 'strict-origin-when-cross-origin';

    function applyLeafletReferrerPolicy() {
        if (typeof L !== 'undefined' && L.TileLayer && L.TileLayer.prototype) {
            L.TileLayer.prototype.options.referrerPolicy = REFERRER_POLICY;
        }
    }

    window.MobMapTiles = {
        url: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
        options: {
            maxZoom: 19,
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
            referrerPolicy: REFERRER_POLICY,
        },
        applyLeafletReferrerPolicy,
    };

    applyLeafletReferrerPolicy();
})();
