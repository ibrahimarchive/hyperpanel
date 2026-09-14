/**
 * HyperPanel — Activity Log Page
 */
let _activityPage = 1;
let _activityCategory = '';

async function renderActivity() {
    const content = document.getElementById('page-content');
    try {
        const params = new URLSearchParams({ page: _activityPage, limit: 50 });
        if (_activityCategory) params.set('category', _activityCategory);
        const data = await API.get(`/api/activity?${params}`);
        const categories = await API.get('/api/activity/categories');
        const stats = await API.get('/api/activity/stats');

        const categoryIcons = { auth: '🔑', website: '🌐', database: '🗄️', domain: '🌍', dns: '📋', ssl: '🔒', firewall: '🛡️', file: '📁', backup: '💾', cron: '⏰', user: '👤', docker: '🐳', service: '⚙️', system: '💻' };

        content.innerHTML = `
            <div class="page-header"><div class="page-header-left"><h1>Activity Log</h1><p>Audit trail of all panel actions</p></div>
            <div class="page-header-actions"><span style="font-size:var(--text-xs);color:var(--text-tertiary)">${stats.recent_24h} actions in last 24h · ${stats.total} total</span></div></div>

            <div style="display:flex;gap:var(--space-2);margin-bottom:var(--space-4);flex-wrap:wrap">
                <button class="btn ${!_activityCategory ? 'btn-primary' : 'btn-ghost'} btn-sm" onclick="filterActivity('')">All</button>
                ${categories.map(c => `<button class="btn ${_activityCategory === c ? 'btn-primary' : 'btn-ghost'} btn-sm" onclick="filterActivity('${c}')">${categoryIcons[c] || '📌'} ${c}</button>`).join('')}
            </div>

            ${data.items.length > 0 ? `<div class="table-wrapper"><table class="table"><thead><tr><th style="width:40px"></th><th>Action</th><th>Description</th><th>User</th><th>Status</th><th>Time</th></tr></thead><tbody>
                ${data.items.map(log => `<tr>
                    <td style="text-align:center">${categoryIcons[log.category] || '📌'}</td>
                    <td><code style="font-size:var(--text-xs);background:var(--bg-tertiary);padding:2px 6px;border-radius:4px">${log.action}</code></td>
                    <td>${log.description}${log.resource_name ? ` <span style="color:var(--text-tertiary);font-size:var(--text-xs)">(${log.resource_name})</span>` : ''}</td>
                    <td style="font-size:var(--text-xs)">${log.user_id ? `User #${log.user_id}` : 'System'}${log.ip_address ? `<br><span style="color:var(--text-tertiary)">${log.ip_address}</span>` : ''}</td>
                    <td><span class="badge ${log.status === 'success' ? 'badge-success' : log.status === 'failed' ? 'badge-danger' : 'badge-warning'}">${log.status}</span></td>
                    <td style="font-size:var(--text-xs);color:var(--text-tertiary);white-space:nowrap">${log.created_at ? new Date(log.created_at).toLocaleString() : '—'}</td>
                </tr>`).join('')}
            </tbody></table></div>

            ${data.pages > 1 ? `<div style="display:flex;justify-content:center;gap:var(--space-2);margin-top:var(--space-4)">
                <button class="btn btn-ghost btn-sm" ${data.page <= 1 ? 'disabled' : ''} onclick="changeActivityPage(${data.page - 1})">← Previous</button>
                <span style="display:flex;align-items:center;font-size:var(--text-xs);color:var(--text-tertiary)">Page ${data.page} of ${data.pages}</span>
                <button class="btn btn-ghost btn-sm" ${data.page >= data.pages ? 'disabled' : ''} onclick="changeActivityPage(${data.page + 1})">Next →</button>
            </div>` : ''}
            ` : `<div class="card"><div class="card-body"><div class="empty-state"><div class="empty-state-icon">📋</div><h3>No activity</h3><p>Actions will appear here as you use the panel.</p></div></div></div>`}`;
    } catch (e) { content.innerHTML = `<div class="empty-state"><h3>Error</h3><p>${e.message}</p></div>`; }
}

function filterActivity(category) { _activityCategory = category; _activityPage = 1; renderActivity(); }
function changeActivityPage(page) { _activityPage = page; renderActivity(); }
