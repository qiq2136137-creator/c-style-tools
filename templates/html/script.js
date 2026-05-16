function initTheme() {
    const saved = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const theme = saved || (prefersDark ? 'dark' : 'light');
    document.documentElement.setAttribute('data-theme', theme);
}

function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
}

function initSearch() {
    const searchBox = document.getElementById('search');
    const searchResults = document.getElementById('search-results');
    if (!searchBox || !searchResults) return;

    const items = [];
    document.querySelectorAll('[data-searchable]').forEach(el => {
        items.push({
            text: el.getAttribute('data-searchable'),
            type: el.getAttribute('data-type') || '',
            element: el
        });
    });

    searchBox.addEventListener('input', function() {
        const query = this.value.toLowerCase().trim();
        if (query.length < 2) {
            searchResults.style.display = 'none';
            return;
        }

        const matches = items.filter(item =>
            item.text.toLowerCase().includes(query) ||
            item.type.toLowerCase().includes(query)
        );

        if (matches.length === 0) {
            searchResults.style.display = 'none';
            return;
        }

        searchResults.innerHTML = matches.slice(0, 20).map(item =>
            '<div class="search-result-item" data-target="' + item.element.id + '">' +
            '<strong>' + item.text + '</strong>' +
            '<span style="color:var(--text-secondary);font-size:0.85em;margin-left:8px">' + item.type + '</span>' +
            '</div>'
        ).join('');
        searchResults.style.display = 'block';

        searchResults.querySelectorAll('.search-result-item').forEach(el => {
            el.addEventListener('click', function() {
                const targetId = this.getAttribute('data-target');
                const target = document.getElementById(targetId);
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    searchResults.style.display = 'none';
                    searchBox.value = '';
                }
            });
        });
    });

    document.addEventListener('click', function(e) {
        if (!searchBox.contains(e.target) && !searchResults.contains(e.target)) {
            searchResults.style.display = 'none';
        }
    });
}

function initSidebarHighlight() {
    const sections = document.querySelectorAll('h2[id], h3[id], h4[id]');
    const navItems = document.querySelectorAll('.nav-item');

    const observer = new IntersectionObserver(entries => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                navItems.forEach(item => item.classList.remove('active'));
                const activeItem = document.querySelector('.nav-item[href="#' + entry.target.id + '"]');
                if (activeItem) activeItem.classList.add('active');
            }
        });
    }, { rootMargin: '-80px 0px -80% 0px' });

    sections.forEach(section => observer.observe(section));
}

document.addEventListener('DOMContentLoaded', function() {
    initTheme();
    initSearch();
    initSidebarHighlight();
});
