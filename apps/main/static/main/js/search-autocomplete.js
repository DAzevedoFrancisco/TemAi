(function () {
    const SUGGESTIONS_URL = '/api/pesquisa/sugestoes/';
    const MIN_CHARS = 1;
    const DEBOUNCE_MS = 220;
    const configs = [
        { input: '.search-form input[name="q"]', wrap: '.search' },
        { input: '.navbar-search-form input[name="q"]', wrap: '.navbar-search-input-wrap' },
    ];

    function debounce(fn, wait) {
        let timer = null;
        return function (...args) {
            window.clearTimeout(timer);
            timer = window.setTimeout(() => fn.apply(this, args), wait);
        };
    }

    function ensurePanel(wrap) {
        let panel = wrap.querySelector('.search-autocomplete');
        if (panel) {
            return panel;
        }

        panel = document.createElement('div');
        panel.className = 'search-autocomplete';
        panel.hidden = true;
        panel.setAttribute('role', 'listbox');
        wrap.appendChild(panel);
        wrap.classList.add('has-autocomplete');
        return panel;
    }

    function hidePanel(panel) {
        panel.hidden = true;
        panel.innerHTML = '';
        panel.dataset.activeIndex = '';
    }

    function renderSuggestions(panel, items, query) {
        if (!items.length) {
            hidePanel(panel);
            return;
        }

        panel.replaceChildren();
        items.forEach((name, index) => {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'search-autocomplete-item';
            button.setAttribute('role', 'option');
            button.dataset.index = String(index);
            button.dataset.value = name;

            const label = document.createElement('span');
            label.className = 'search-autocomplete-name';
            label.textContent = name;

            const hint = document.createElement('span');
            hint.className = 'search-autocomplete-hint';
            hint.textContent = 'Pesquisar';

            button.append(label, hint);
            panel.appendChild(button);
        });
        panel.hidden = false;
        panel.dataset.activeIndex = '0';
        highlightActive(panel);
        panel.dataset.query = query;
    }

    function highlightActive(panel) {
        const items = [...panel.querySelectorAll('.search-autocomplete-item')];
        const activeIndex = Number(panel.dataset.activeIndex || 0);
        items.forEach((item, index) => {
            item.classList.toggle('is-active', index === activeIndex);
        });
    }

    function moveActive(panel, delta) {
        const items = panel.querySelectorAll('.search-autocomplete-item');
        if (!items.length) {
            return;
        }
        const current = Number(panel.dataset.activeIndex || 0);
        const next = (current + delta + items.length) % items.length;
        panel.dataset.activeIndex = String(next);
        highlightActive(panel);
        items[next].scrollIntoView({ block: 'nearest' });
    }

    function selectActive(panel, input, form) {
        const items = panel.querySelectorAll('.search-autocomplete-item');
        if (!items.length) {
            return false;
        }
        const activeIndex = Number(panel.dataset.activeIndex || 0);
        const item = items[activeIndex];
        if (!item) {
            return false;
        }
        input.value = item.dataset.value || item.textContent.trim();
        hidePanel(panel);
        if (form) {
            form.requestSubmit ? form.requestSubmit() : form.submit();
        }
        return true;
    }

    configs.forEach(({ input: inputSelector, wrap: wrapSelector }) => {
        document.querySelectorAll(inputSelector).forEach((input) => {
            const wrap = input.closest(wrapSelector);
            if (!wrap) {
                return;
            }

            const form = input.closest('form');
            const panel = ensurePanel(wrap);
            let requestId = 0;

            const fetchSuggestions = debounce(async () => {
                const query = input.value.trim();
                if (query.length < MIN_CHARS) {
                    hidePanel(panel);
                    return;
                }

                const currentRequest = ++requestId;
                try {
                    const response = await fetch(
                        `${SUGGESTIONS_URL}?q=${encodeURIComponent(query)}`,
                        { headers: { Accept: 'application/json' } }
                    );
                    if (!response.ok) {
                        hidePanel(panel);
                        return;
                    }
                    const data = await response.json();
                    if (currentRequest !== requestId) {
                        return;
                    }
                    renderSuggestions(panel, data.suggestions || [], query);
                } catch (_error) {
                    if (currentRequest === requestId) {
                        hidePanel(panel);
                    }
                }
            }, DEBOUNCE_MS);

            input.setAttribute('autocomplete', 'off');
            input.setAttribute('aria-autocomplete', 'list');

            input.addEventListener('input', fetchSuggestions);
            input.addEventListener('focus', fetchSuggestions);

            input.addEventListener('keydown', (event) => {
                if (panel.hidden) {
                    return;
                }
                if (event.key === 'ArrowDown') {
                    event.preventDefault();
                    moveActive(panel, 1);
                } else if (event.key === 'ArrowUp') {
                    event.preventDefault();
                    moveActive(panel, -1);
                } else if (event.key === 'Enter') {
                    if (selectActive(panel, input, form)) {
                        event.preventDefault();
                    }
                } else if (event.key === 'Escape') {
                    hidePanel(panel);
                }
            });

            panel.addEventListener('mousedown', (event) => {
                const item = event.target.closest('.search-autocomplete-item');
                if (!item) {
                    return;
                }
                event.preventDefault();
                input.value = item.dataset.value || item.textContent.trim();
                hidePanel(panel);
                if (form) {
                    form.requestSubmit ? form.requestSubmit() : form.submit();
                }
            });

            document.addEventListener('click', (event) => {
                if (!wrap.contains(event.target)) {
                    hidePanel(panel);
                }
            });
        });
    });
})();
