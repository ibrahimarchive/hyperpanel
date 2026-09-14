/**
 * HyperPanel — Dashboard Page
 */

async function renderDashboard() {
    const content = document.getElementById('page-content');

    try {
        const stats = await API.get('/api/dashboard/stats');
        const activity = await API.get('/api/dashboard/activity');

        const cpuColor = stats.cpu.usage_percent > 80 ? 'danger' : stats.cpu.usage_percent > 60 ? 'warning' : 'success';
        const memColor = stats.memory.usage_percent > 80 ? 'danger' : stats.memory.usage_percent > 60 ? 'warning' : 'success';
        const diskColor = stats.disk.usage_percent > 80 ? 'danger' : stats.disk.usage_percent > 60 ? 'warning' : 'success';

        content.innerHTML = `
            <div class="page-header">
                <div class="page-header-left">
                    <h1>Dashboard</h1>
                    <p>Welcome back! Here's your server overview.</p>
                </div>
            </div>

            <!-- Quick Resource Stats -->
            <div class="quick-stats">
                <div class="quick-stat">
                    <div class="quick-stat-icon" style="background: rgba(99,102,241,0.1); color: var(--accent-400);">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="2" width="20" height="8" rx="2" ry="2"/><rect x="2" y="14" width="20" height="8" rx="2" ry="2"/><line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/></svg>
                    </div>
                    <div class="quick-stat-info">
                        <div class="quick-stat-value">${stats.websites_count}</div>
                        <div class="quick-stat-label">Websites</div>
                    </div>
                </div>
                <div class="quick-stat">
                    <div class="quick-stat-icon" style="background: rgba(34,197,94,0.1); color: var(--success-400);">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/></svg>
                    </div>
                    <div class="quick-stat-info">
                        <div class="quick-stat-value">${stats.databases_count}</div>
                        <div class="quick-stat-label">Databases</div>
                    </div>
                </div>
                <div class="quick-stat">
                    <div class="quick-stat-icon" style="background: rgba(245,158,11,0.1); color: var(--warning-400);">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 014 10 15.3 15.3 0 01-4 10 15.3 15.3 0 01-4-10 15.3 15.3 0 014-10z"/></svg>
                    </div>
                    <div class="quick-stat-info">
                        <div class="quick-stat-value">${stats.domains_count}</div>
                        <div class="quick-stat-label">Domains</div>
                    </div>
                </div>
                <div class="quick-stat">
                    <div class="quick-stat-icon" style="background: rgba(239,68,68,0.1); color: var(--danger-400);">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87M16 3.13a4 4 0 010 7.75"/></svg>
                    </div>
                    <div class="quick-stat-info">
                        <div class="quick-stat-value">${stats.users_count}</div>
                        <div class="quick-stat-label">Users</div>
                    </div>
                </div>
            </div>

            <!-- System Resource Cards -->
            <div class="grid grid-4" style="margin-bottom: var(--space-6);">
                <div class="stat-card" style="--stat-color: var(--accent-500);">
                    <div class="stat-card-header">
                        <span class="stat-card-label">CPU Usage</span>
                        <div class="stat-card-icon">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><path d="M15 2v2M15 20v2M2 15h2M2 9h2M20 15h2M20 9h2M9 2v2M9 20v2"/></svg>
                        </div>
                    </div>
                    <div class="stat-card-value">${stats.cpu.usage_percent}%</div>
                    <div class="stat-card-sub">${stats.cpu.cores} cores · Load: ${stats.cpu.load_avg_1}</div>
                    <div class="progress">
                        <div class="progress-bar ${cpuColor}" style="width: ${stats.cpu.usage_percent}%"></div>
                    </div>
                </div>

                <div class="stat-card" style="--stat-color: var(--success-500);">
                    <div class="stat-card-header">
                        <span class="stat-card-label">Memory</span>
                        <div class="stat-card-icon">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 19v-8a6 6 0 0112 0v8"/><path d="M6 15a6 6 0 0012 0"/></svg>
                        </div>
                    </div>
                    <div class="stat-card-value">${stats.memory.usage_percent}%</div>
                    <div class="stat-card-sub">${stats.memory.used_mb.toFixed(0)} / ${stats.memory.total_mb.toFixed(0)} MB</div>
                    <div class="progress">
                        <div class="progress-bar ${memColor}" style="width: ${stats.memory.usage_percent}%"></div>
                    </div>
                </div>

                <div class="stat-card" style="--stat-color: var(--warning-500);">
                    <div class="stat-card-header">
                        <span class="stat-card-label">Disk</span>
                        <div class="stat-card-icon">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z"/></svg>
                        </div>
                    </div>
                    <div class="stat-card-value">${stats.disk.usage_percent}%</div>
                    <div class="stat-card-sub">${stats.disk.used_gb} / ${stats.disk.total_gb} GB</div>
                    <div class="progress">
                        <div class="progress-bar ${diskColor}" style="width: ${stats.disk.usage_percent}%"></div>
                    </div>
                </div>

                <div class="stat-card" style="--stat-color: var(--info-500);">
                    <div class="stat-card-header">
                        <span class="stat-card-label">Network</span>
                        <div class="stat-card-icon">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                        </div>
                    </div>
                    <div class="stat-card-value">${stats.network.bandwidth_in_mbps} Mbps</div>
                    <div class="stat-card-sub">↓ ${formatBytes(stats.network.bytes_recv)} · ↑ ${formatBytes(stats.network.bytes_sent)}</div>
                </div>
            </div>

            <!-- Services & Activity -->
            <div class="dashboard-services">
                <div class="card">
                    <div class="card-header">
                        <h3>Services</h3>
                        <span class="badge badge-neutral">${stats.services.filter(s => s.status !== 'not-found').length} tracked</span>
                    </div>
                    <div class="card-body" style="padding: var(--space-2);">
                        <div class="service-list">
                            ${stats.services.filter(s => s.status !== 'not-found').map(s => `
                                <div class="service-item">
                                    <div class="service-item-left">
                                        <div class="service-item-icon">${getServiceIcon(s.name)}</div>
                                        <div>
                                            <div class="service-item-name">${s.display_name}</div>
                                            <div class="service-item-sub">${s.name}</div>
                                        </div>
                                    </div>
                                    <span class="status-dot ${s.active ? 'online' : 'offline'}"></span>
                                </div>
                            `).join('')}
                            ${stats.services.filter(s => s.status !== 'not-found').length === 0 ? '<div style="padding: var(--space-4); text-align: center; color: var(--text-tertiary); font-size: var(--text-sm);">No services detected</div>' : ''}
                        </div>
                    </div>
                </div>

                <div class="card">
                    <div class="card-header">
                        <h3>Recent Activity</h3>
                        <span class="badge badge-neutral">${activity.length} events</span>
                    </div>
                    <div class="card-body" style="padding: 0;">
                        <div class="activity-list">
                            ${activity.length > 0 ? activity.slice(0, 8).map(a => `
                                <div class="activity-item">
                                    <div class="activity-dot" style="background: ${a.status === 'success' ? 'var(--success-500)' : 'var(--danger-500)'}"></div>
                                    <div class="activity-content">
                                        <div class="activity-text">${a.description}</div>
                                        <div class="activity-time">${timeAgo(a.created_at)}</div>
                                    </div>
                                </div>
                            `).join('') : `
                                <div style="padding: var(--space-8); text-align: center; color: var(--text-tertiary); font-size: var(--text-sm);">
                                    No recent activity
                                </div>
                            `}
                        </div>
                    </div>
                </div>
            </div>

            <!-- System Info -->
            <div class="card" style="margin-top: var(--space-5);">
                <div class="card-header">
                    <h3>System Information</h3>
                    <span class="badge badge-success">
                        <span class="status-dot online" style="width:6px;height:6px;"></span>
                        Uptime: ${stats.system_info.uptime_human}
                    </span>
                </div>
                <div class="card-body">
                    <div class="grid grid-4" style="gap: var(--space-4);">
                        <div>
                            <div style="font-size: var(--text-xs); color: var(--text-tertiary); margin-bottom: 4px;">Hostname</div>
                            <div style="font-weight: var(--font-medium); font-size: var(--text-sm);">${stats.system_info.hostname}</div>
                        </div>
                        <div>
                            <div style="font-size: var(--text-xs); color: var(--text-tertiary); margin-bottom: 4px;">OS</div>
                            <div style="font-weight: var(--font-medium); font-size: var(--text-sm);">${stats.system_info.os_name}</div>
                        </div>
                        <div>
                            <div style="font-size: var(--text-xs); color: var(--text-tertiary); margin-bottom: 4px;">Kernel</div>
                            <div style="font-weight: var(--font-medium); font-size: var(--text-sm);">${stats.system_info.kernel}</div>
                        </div>
                        <div>
                            <div style="font-size: var(--text-xs); color: var(--text-tertiary); margin-bottom: 4px;">Panel Version</div>
                            <div style="font-weight: var(--font-medium); font-size: var(--text-sm);">v${stats.system_info.panel_version}</div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    } catch (e) {
        content.innerHTML = `
            <div class="page-header"><div class="page-header-left"><h1>Dashboard</h1><p>Welcome to HyperPanel</p></div></div>
            <div class="card"><div class="card-body">
                <div class="empty-state">
                    <div class="empty-state-icon">📊</div>
                    <h3>Could not load stats</h3>
                    <p>${e.message}</p>
                    <button class="btn btn-primary" onclick="renderDashboard()">Retry</button>
                </div>
            </div></div>
        `;
    }
}

function getServiceIcon(name) {
    const icons = {
        nginx: '🌐', mysql: '🗄️', mariadb: '🗄️', docker: '🐳',
        ufw: '🛡️', cron: '⏰', ssh: '🔑', postfix: '📧',
    };
    const key = Object.keys(icons).find(k => name.includes(k));
    return key ? icons[key] : '⚙️';
}

function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function timeAgo(dateStr) {
    if (!dateStr) return '';
    const now = new Date();
    const date = new Date(dateStr);
    const seconds = Math.floor((now - date) / 1000);

    if (seconds < 60) return 'Just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
}
