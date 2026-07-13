(function () {
    function parseNumber(value) {
        const parsed = Number.parseFloat(value);
        return Number.isFinite(parsed) ? parsed : null;
    }

    function configureLeafletIcons(mapEl) {
        if (typeof L === 'undefined' || !L.Icon || !L.Icon.Default) {
            return;
        }

        const iconUrl = mapEl.dataset.markerIcon;
        const iconRetinaUrl = mapEl.dataset.markerIcon2x;
        const shadowUrl = mapEl.dataset.markerShadow;

        if (!iconUrl) {
            return;
        }

        delete L.Icon.Default.prototype._getIconUrl;
        L.Icon.Default.mergeOptions({
            iconUrl,
            iconRetinaUrl: iconRetinaUrl || iconUrl,
            shadowUrl: shadowUrl || '',
        });
    }

    function getScrollRoot() {
        const scrollRoot = document.querySelector('.admin-panel-body .dash-content');
        if (!scrollRoot) {
            return null;
        }

        const style = window.getComputedStyle(scrollRoot);
        const scrollable = scrollRoot.scrollHeight > scrollRoot.clientHeight + 1;
        const allowsScroll = style.overflowY === 'auto' || style.overflowY === 'scroll' || style.overflowY === 'overlay';

        return scrollable && allowsScroll ? scrollRoot : null;
    }

    function bootAdminEstablishmentMap() {
        const mapEl = document.getElementById('admin-est-detail-map');
        if (!mapEl || mapEl.dataset.mapReady === 'true') {
            return;
        }

        const lat = parseNumber(mapEl.dataset.lat);
        const lng = parseNumber(mapEl.dataset.lng);
        const name = mapEl.dataset.name || '';

        if (lat == null || lng == null || typeof MobLocationMap === 'undefined' || typeof L === 'undefined') {
            return;
        }

        configureLeafletIcons(mapEl);

        const map = MobLocationMap.init('admin-est-detail-map', {
            markers: [{
                lat,
                lng,
                popup: name,
            }],
            defaultZoom: 15,
            openFirstPopup: true,
            preferCanvas: false,
        });

        if (!map) {
            return;
        }

        mapEl.dataset.mapReady = 'true';

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

        const scrollRoot = getScrollRoot();
        const onScroll = () => refresh();
        window.addEventListener('scroll', onScroll, { passive: true });
        scrollRoot?.addEventListener('scroll', onScroll, { passive: true });

        if (typeof ResizeObserver !== 'undefined') {
            const resizeObserver = new ResizeObserver(refresh);
            resizeObserver.observe(mapEl);
        }
    }

    function tryBootAdminEstablishmentMap() {
        window.requestAnimationFrame(bootAdminEstablishmentMap);
    }

    function watchAdminEstablishmentMap() {
        const mapEl = document.getElementById('admin-est-detail-map');
        if (!mapEl) {
            return;
        }

        let attempts = 0;
        const maxAttempts = 20;

        const attemptBoot = () => {
            if (mapEl.dataset.mapReady === 'true') {
                return;
            }

            attempts += 1;
            tryBootAdminEstablishmentMap();

            if (mapEl.dataset.mapReady === 'true' || attempts >= maxAttempts) {
                return;
            }

            window.setTimeout(attemptBoot, 250);
        };

        if ('IntersectionObserver' in window) {
            const scrollRoot = getScrollRoot();
            const observer = new IntersectionObserver((entries) => {
                entries.forEach((entry) => {
                    if (entry.isIntersecting) {
                        attemptBoot();
                    }
                });
            }, {
                root: scrollRoot,
                threshold: 0.05,
                rootMargin: '120px 0px',
            });

            observer.observe(mapEl);
        }

        const scrollRoot = getScrollRoot();
        const onScroll = () => attemptBoot();
        window.addEventListener('scroll', onScroll, { passive: true });
        scrollRoot?.addEventListener('scroll', onScroll, { passive: true });

        const start = () => {
            attemptBoot();
            window.setTimeout(attemptBoot, 700);
            window.setTimeout(attemptBoot, 1500);
        };

        if (document.readyState === 'complete') {
            start();
        } else {
            window.addEventListener('load', start, { once: true });
        }
    }

    watchAdminEstablishmentMap();
})();
