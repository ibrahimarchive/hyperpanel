/**
 * HyperPanel — Main Application Controller
 * Initializes sidebar, routes, theme, and auth.
 */

// ── Navigation Config ────────────────────────────────────
const NAV_ITEMS = [
    {
        section: 'Overview',
        items: [
            { route: '/dashboard', label: 'Dashboard', icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/></svg>' },
            { route: '/monitoring', label: 'Monitoring', icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>' },
        ]
    },
    {
        section: 'Hosting',
        items: [
            { route: '/websites', label: 'Websites', icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10 15.3 15.3 0 01-4-10 15.3 15.3 0 014-10z"/></svg>' },
            { route: '/databases', label: 'Databases', icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>' },
            { route: '/domains', label: 'Domains', icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>' },
            { route: '/dns', label: 'DNS', icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 2l-2 2m-7.61 7.61a5.5 5.5 0 11-7.778 7.778 5.5 5.5 0 017.777-7.777zm0 0L15.5 7.5m0 0l3 3L22 7l-3-3m-3.5 3.5L19 4"/></svg>' },
            { route: '/ssl', label: 'SSL / TLS', icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0110 0v4"/></svg>' },
            { route: '/email', label: 'Mail Server', icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>' },
            { route: '/ftp', label: 'FTP Accounts', icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 14.899A7 7 0 1 1 15.71 8h1.79a4.5 4.5 0 0 1 2.5 8.242"/><path d="M12 12v9"/><path d="m16 16-4-4-4 4"/></svg>' },
        ]
    },
    {
        section: 'Tools',
        items: [
            { route: '/files', label: 'File Manager', icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/></svg>' },
            { route: '/docker', label: 'Docker', icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M2 12h20"/><path d="M20 12v3a6 6 0 0 1-6 6H7a5 5 0 0 1-5-5v-4"/><rect x="4" y="8" width="4" height="4"/><rect x="10" y="8" width="4" height="4"/><rect x="16" y="8" width="4" height="4"/><rect x="10" y="4" width="4" height="4"/></svg>' },
            { route: '/backups', label: 'Backups', icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg>' },
            { route: '/cron', label: 'Cron Jobs', icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>' },
            { route: '/services', label: 'Services', icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="2" width="20" height="8" rx="2" ry="2"/><rect x="2" y="14" width="20" height="8" rx="2" ry="2"/><line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/></svg>' },
            { route: '/processes', label: 'Processes', icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 17l6-6-6-6"/><path d="M12 19h8"/></svg>' },
            { route: '/logs', label: 'Logs', icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><path d="M14 2v6h6M16 13H8M16 17H8M10 9H8"/></svg>' },
            { route: '/terminal', label: 'Terminal', icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg>' },
            { route: '/firewall', label: 'Firewall', icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>' },
            { route: '/fail2ban', label: 'Fail2Ban', icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0110 0v4"/></svg>' },
        ]
    },
    {
        section: 'Admin',
        items: [
            { route: '/activity', label: 'Audit Log', icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 8v4l3 3"/><circle cx="12" cy="12" r="9"/></svg>', admin: true },
            { route: '/users', label: 'Users', icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75"/></svg>', admin: true },
            { route: '/settings', label: 'Settings', icon: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z"/></svg>' },
        ]
    },
];


// ── Build Sidebar ────────────────────────────────────────
function buildSidebar() {
    const nav = document.getElementById('sidebar-nav');
    if (!nav) return;

    let html = '';
    NAV_ITEMS.forEach(section => {
        html += `<div class="sidebar-section"><div class="sidebar-section-title">${section.section}</div>`;
        section.items.forEach(item => {
            if (item.admin && !isAdmin()) return;
            html += `
                <div class="nav-item" data-route="${item.route}" onclick="window.location.hash='#${item.route}'">
                    <span class="nav-item-icon">${item.icon}</span>
                    <span class="nav-item-label">${item.label}</span>
                </div>
            `;
        });
        html += '</div>';
    });

    nav.innerHTML = html;
}


// ── Register Routes ──────────────────────────────────────
function registerRoutes() {
    Router.register('/dashboard', renderDashboard);
    Router.register('/websites', renderWebsites);
    Router.register('/databases', renderDatabases);
    Router.register('/domains', renderDomains);
    Router.register('/dns', renderDNS);
    Router.register('/ssl', renderSSL);
    Router.register('/email', typeof renderEmail === 'function' ? renderEmail : () => {});
    Router.register('/ftp', typeof renderFTP === 'function' ? renderFTP : () => {});
    Router.register('/files', renderFiles);
    Router.register('/docker', typeof renderDocker === 'function' ? renderDocker : () => {});
    Router.register('/firewall', renderFirewall);
    Router.register('/monitoring', renderMonitoring);
    Router.register('/backups', typeof renderBackups === 'function' ? renderBackups : () => {});
    Router.register('/cron', typeof renderCron === 'function' ? renderCron : () => {});
    Router.register('/services', typeof renderServices === 'function' ? renderServices : () => {});
    Router.register('/processes', typeof renderProcesses === 'function' ? renderProcesses : () => {});
    Router.register('/logs', typeof renderLogs === 'function' ? renderLogs : () => {});
    Router.register('/fail2ban', typeof renderFail2ban === 'function' ? renderFail2ban : () => {});
    Router.register('/terminal', typeof renderTerminal === 'function' ? renderTerminal : () => {});
    Router.register('/activity', typeof renderActivity === 'function' ? renderActivity : () => {});
    Router.register('/users', renderUsers);
    Router.register('/settings', renderSettings);
}


// ── Sidebar Collapse ─────────────────────────────────────
function initSidebarCollapse() {
    const sidebar = document.getElementById('sidebar');
    const collapseBtn = document.getElementById('sidebar-collapse-btn');
    const toggleBtn = document.getElementById('topbar-menu-toggle');

    const saved = localStorage.getItem('hyperpanel-sidebar-collapsed');
    if (saved === 'true') sidebar.classList.add('collapsed');

    if (collapseBtn) {
        collapseBtn.addEventListener('click', () => {
            sidebar.classList.toggle('collapsed');
            localStorage.setItem('hyperpanel-sidebar-collapsed', sidebar.classList.contains('collapsed'));
        });
    }

    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            sidebar.classList.toggle('collapsed');
            localStorage.setItem('hyperpanel-sidebar-collapsed', sidebar.classList.contains('collapsed'));
        });
    }
}


// ── User Dropdown ────────────────────────────────────────
function initDropdowns() {
    const userDropdown = document.getElementById('user-dropdown');
    if (userDropdown) {
        userDropdown.addEventListener('click', (e) => {
            e.stopPropagation();
            userDropdown.classList.toggle('open');
        });

        document.addEventListener('click', () => {
            userDropdown.classList.remove('open');
        });
    }
}


// ── Keyboard Shortcuts ───────────────────────────────────
function initKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        // Ctrl+K → Focus search
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            document.getElementById('search-input')?.focus();
        }
    });
}


// ── App Initialization ───────────────────────────────────
async function initApp() {
    // Initialize theme
    initTheme();

    // Check authentication
    const authed = await checkAuth();
    if (!authed) return;

    // Build UI
    buildSidebar();
    initSidebarCollapse();
    initDropdowns();
    initKeyboardShortcuts();

    // Register routes and start router
    registerRoutes();
    Router.init();

    // Check for official releases silently in background
    setTimeout(async () => {
        try {
            const update = await API.get('/api/updates/check');
            if (update && update.has_update) {
                const badge = document.getElementById('notification-badge');
                if (badge) {
                    badge.style.display = 'block';
                    badge.title = `New release ${update.tag_name} available!`;
                }
                const settingsItem = document.querySelector('[data-route="/settings"]');
                if (settingsItem && !settingsItem.querySelector('.update-dot')) {
                    const dot = document.createElement('span');
                    dot.className = 'update-dot';
                    dot.style.cssText = 'width:7px;height:7px;border-radius:50%;background:var(--primary-400);margin-left:auto;display:inline-block;box-shadow:0 0 8px var(--primary-400);';
                    dot.title = `Update available: ${update.tag_name}`;
                    settingsItem.appendChild(dot);
                }
            }
        } catch (e) {
            // Silently ignore
        }
    }, 2500);
}

// Start the app
initApp();

