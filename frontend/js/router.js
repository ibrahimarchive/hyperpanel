/**
 * HyperPanel — Client-side Hash Router
 */

const Router = {
    routes: {},
    currentRoute: null,

    register(path, handler) {
        this.routes[path] = handler;
    },

    async navigate(path) {
        if (this.currentRoute === path) return;
        this.currentRoute = path;

        const handler = this.routes[path];
        if (handler) {
            const content = document.getElementById('page-content');
            content.innerHTML = '<div style="display:flex;align-items:center;justify-content:center;height:40vh;"><div class="spinner spinner-lg"></div></div>';

            try {
                await handler();
            } catch (e) {
                console.error('Page load error:', e);
                content.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-state-icon">⚠️</div>
                        <h3>Error Loading Page</h3>
                        <p>${e.message}</p>
                    </div>
                `;
            }

            // Update active nav item
            document.querySelectorAll('.nav-item').forEach(item => {
                item.classList.toggle('active', item.dataset.route === path);
            });

            // Update breadcrumb
            const pageNames = {
                '/dashboard': 'Dashboard',
                '/websites': 'Websites',
                '/databases': 'Databases',
                '/domains': 'Domains',
                '/dns': 'DNS',
                '/ssl': 'SSL / TLS',
                '/files': 'File Manager',
                '/firewall': 'Firewall',
                '/monitoring': 'Monitoring',
                '/users': 'Users',
                '/settings': 'Settings',
            };

            const breadcrumb = document.getElementById('topbar-breadcrumb');
            if (breadcrumb) {
                breadcrumb.innerHTML = `
                    <span>${pageNames[path] || path}</span>
                `;
            }

            // Update page title
            document.title = `${pageNames[path] || 'HyperPanel'} — HyperPanel`;
        }
    },

    init() {
        // Listen for hash changes
        window.addEventListener('hashchange', () => {
            const path = window.location.hash.replace('#', '') || '/dashboard';
            this.navigate(path);
        });

        // Navigate to initial route
        const initial = window.location.hash.replace('#', '') || '/dashboard';
        this.navigate(initial);
    },
};
