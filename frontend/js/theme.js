/**
 * HyperPanel — Theme Manager
 * Dark/Light mode toggle with localStorage persistence.
 */

function initTheme() {
    const saved = localStorage.getItem('hyperpanel-theme') || 'dark';
    document.documentElement.setAttribute('data-theme', saved);
    updateThemeIcons(saved);

    const toggleBtn = document.getElementById('theme-toggle');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            const current = document.documentElement.getAttribute('data-theme');
            const next = current === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', next);
            localStorage.setItem('hyperpanel-theme', next);
            updateThemeIcons(next);
        });
    }
}

function updateThemeIcons(theme) {
    const sun = document.getElementById('theme-icon-sun');
    const moon = document.getElementById('theme-icon-moon');
    if (sun && moon) {
        sun.style.display = theme === 'dark' ? 'block' : 'none';
        moon.style.display = theme === 'light' ? 'block' : 'none';
    }
}
