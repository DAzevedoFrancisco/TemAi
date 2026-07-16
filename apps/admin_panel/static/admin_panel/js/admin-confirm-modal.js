/**
 * @deprecated Use main/js/dash-confirm-modal.js (loaded from admin/vendor base).
 * Kept as a no-op shim so old template references do not break.
 */
(function () {
    if (typeof window.MobDashConfirm === 'undefined') {
        console.warn('[Mob] admin-confirm-modal.js is deprecated; load main/js/dash-confirm-modal.js instead.');
    }
})();
