(function () {
    const configs = [
        { input: '.search-form input[name="q"]', wrap: '.search', clearTarget: '.search-input-row' },
        { input: '.navbar-search-form input[name="q"]', wrap: '.navbar-search-input-wrap' },
    ];

    function hasQuery(input) {
        return input.value.trim().length > 0;
    }

    const PLACEHOLDER_PHRASES = [
        'Encontre o que precisas perto de ti',
        'Pizza na Beira...',
        'Cabeleireiro perto de ti...',
        'Farmácia aberta agora...',
        'Restaurante com entrega...',
        'Mecânico na tua zona...',
    ];

    function getTypewriterPhrases(input) {
        const fromData = (input.dataset.typewriterPhrases || '')
            .split('|')
            .map((phrase) => phrase.trim())
            .filter(Boolean);

        if (fromData.length) {
            return fromData;
        }

        const fromPlaceholder = (input.getAttribute('placeholder') || '').trim();
        if (fromPlaceholder && !PLACEHOLDER_PHRASES.includes(fromPlaceholder)) {
            return [fromPlaceholder, ...PLACEHOLDER_PHRASES];
        }

        return PLACEHOLDER_PHRASES;
    }

    function initPlaceholderTypewriter(input) {
        const phrases = getTypewriterPhrases(input);
        if (!phrases.length) {
            return { pause() {}, resume() {} };
        }

        let timer = null;
        let phraseIndex = 0;
        let charIndex = 0;
        let isDeleting = false;
        let fullText = phrases[0];

        const typeSpeed = 58;
        const deleteSpeed = 32;
        const pauseEnd = 2200;
        const pauseStart = 480;

        function clearTimer() {
            if (timer !== null) {
                clearTimeout(timer);
                timer = null;
            }
        }

        function shouldAnimate() {
            return document.activeElement !== input && !hasQuery(input);
        }

        function schedule(next, delay) {
            clearTimer();
            timer = setTimeout(next, delay);
        }

        function tick() {
            if (!shouldAnimate()) {
                clearTimer();
                return;
            }

            fullText = phrases[phraseIndex];

            if (!isDeleting) {
                charIndex += 1;
                input.placeholder = fullText.slice(0, charIndex);

                if (charIndex >= fullText.length) {
                    schedule(() => {
                        isDeleting = true;
                        tick();
                    }, pauseEnd);
                    return;
                }

                schedule(tick, typeSpeed);
                return;
            }

            charIndex -= 1;
            input.placeholder = fullText.slice(0, charIndex);

            if (charIndex <= 0) {
                isDeleting = false;
                phraseIndex = (phraseIndex + 1) % phrases.length;
                schedule(tick, pauseStart);
                return;
            }

            schedule(tick, deleteSpeed);
        }

        function pause({ restoreFull = false } = {}) {
            clearTimer();
            if (restoreFull) {
                input.placeholder = phrases[phraseIndex];
            }
        }

        function resume() {
            if (!shouldAnimate()) {
                return;
            }

            charIndex = 0;
            isDeleting = false;
            input.placeholder = '';
            tick();
        }

        input.setAttribute('aria-label', 'Pesquisar produtos e serviços perto de si');
        input.placeholder = '';
        resume();

        input.addEventListener('focus', () => {
            pause({ restoreFull: true });
        });

        input.addEventListener('blur', () => {
            if (!hasQuery(input)) {
                resume();
            }
        });

        return { pause, resume };
    }

    function createClearButton() {
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'search-clear-btn';
        button.setAttribute('aria-label', 'Limpar pesquisa');
        button.hidden = true;
        button.innerHTML = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" aria-hidden="true"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>';
        return button;
    }

    configs.forEach(({ input: inputSelector, wrap: wrapSelector, clearTarget }) => {
        document.querySelectorAll(inputSelector).forEach((input) => {
            const wrap = input.closest(wrapSelector);
            if (!wrap) {
                return;
            }

            const form = input.closest('form');
            const submitBtn = wrap.querySelector('.search-submit, .navbar-search-submit');
            const clearBtn = createClearButton();
            const clearContainer = clearTarget ? wrap.querySelector(clearTarget) : null;
            const typewriter = initPlaceholderTypewriter(input);

            if (clearContainer) {
                clearContainer.appendChild(clearBtn);
            } else {
                const boxImg = wrap.querySelector('.box-img');

                if (boxImg && submitBtn) {
                    boxImg.insertBefore(clearBtn, submitBtn);
                } else if (submitBtn) {
                    wrap.insertBefore(clearBtn, submitBtn);
                } else {
                    wrap.appendChild(clearBtn);
                }
            }

            function syncSearchState() {
                const hasText = hasQuery(input);
                wrap.classList.toggle('has-search-text', hasText);
                clearBtn.hidden = !hasText;
                if (submitBtn) {
                    submitBtn.disabled = !hasText;
                }
            }

            clearBtn.addEventListener('click', () => {
                input.value = '';
                syncSearchState();
                input.focus();
                typewriter.pause({ restoreFull: true });
            });

            input.addEventListener('input', () => {
                syncSearchState();
                if (hasQuery(input)) {
                    typewriter.pause();
                } else if (document.activeElement !== input) {
                    typewriter.resume();
                }
            });
            input.addEventListener('change', syncSearchState);
            syncSearchState();

            if (form) {
                form.addEventListener('submit', (event) => {
                    if (!hasQuery(input)) {
                        event.preventDefault();
                        input.focus();
                    }
                });
            }

            if (submitBtn) {
                submitBtn.addEventListener('click', (event) => {
                    if (!hasQuery(input)) {
                        event.preventDefault();
                        input.focus();
                    }
                });
            }
        });
    });
})();
