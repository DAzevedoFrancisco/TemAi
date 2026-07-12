(function () {
    function paintStars(ratingEl, value) {
        const labels = ratingEl.querySelectorAll('label');
        labels.forEach((label, index) => {
            label.classList.toggle('is-active', index < value);
        });
        ratingEl.dataset.rating = value || '';

        const valueEl = ratingEl.parentElement?.querySelector('.star-rating-value');
        if (valueEl) {
            if (value) {
                valueEl.hidden = false;
                valueEl.textContent = value === 1 ? '1 estrela' : `${value} estrelas`;
            } else {
                valueEl.hidden = true;
                valueEl.textContent = '';
            }
        }
    }

    function initStarRating(ratingEl) {
        const inputs = ratingEl.querySelectorAll('input[type="radio"]');
        const labels = ratingEl.querySelectorAll('label');

        inputs.forEach((input) => {
            input.addEventListener('change', () => {
                paintStars(ratingEl, parseInt(input.value, 10));
            });
        });

        labels.forEach((label, index) => {
            label.addEventListener('mouseenter', () => {
                paintStars(ratingEl, index + 1);
            });
        });

        ratingEl.addEventListener('mouseleave', () => {
            const checked = ratingEl.querySelector('input[type="radio"]:checked');
            paintStars(ratingEl, checked ? parseInt(checked.value, 10) : 0);
        });

        const checked = ratingEl.querySelector('input[type="radio"]:checked');
        if (checked) {
            paintStars(ratingEl, parseInt(checked.value, 10));
        }
    }

    document.querySelectorAll('.star-rating').forEach(initStarRating);
})();
