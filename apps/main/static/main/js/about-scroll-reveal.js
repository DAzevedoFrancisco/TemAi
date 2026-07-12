(function () {
    const aboutSection = document.querySelector('.box-about .about');
    if (!aboutSection) {
        return;
    }

    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const revealItems = [
        aboutSection.querySelector('.about-title'),
        ...aboutSection.querySelectorAll('.about-text h4, .about-text p'),
    ].filter(Boolean);

    if (!revealItems.length) {
        return;
    }

    if (prefersReducedMotion) {
        revealItems.forEach((item) => item.classList.add('about-reveal', 'is-visible'));
        return;
    }

    revealItems.forEach((item, index) => {
        item.classList.add('about-reveal');
        item.style.transitionDelay = `${index * 0.12}s`;
    });

    const observer = new IntersectionObserver(
        (entries) => {
            entries.forEach((entry) => {
                if (!entry.isIntersecting) {
                    return;
                }

                revealItems.forEach((item) => item.classList.add('is-visible'));
                observer.disconnect();
            });
        },
        {
            threshold: 0.18,
            rootMargin: '0px 0px -6% 0px',
        }
    );

    observer.observe(aboutSection);
})();
