/**
 * HyperPanel — Backups Page
 */
async function renderBackups() {
    const content = document.getElementById('page-content');
    try {
        const backups = await API.get('/api/backups');
        const storage = await API.get('/api/backups/storage');

        const usedMB = (storage.used_bytes / 1024 / 1024).toFixed(1);
        const freeMB = (storage.disk_free_bytes / 1024 / 1024 / 1024).toFixed(1);

        content.innerHTML = `
            <div class="page-header"><div class="page-header-left"><h1>Backups</h1><p>Backup and restore your server data</p></div>
            <div class="page-header-actions"><button class="btn btn-primary" onclick="showCreateBackupModal()"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg> Create Backup</button></div></div>

            <div class="grid grid-3" style="margin-bottom:var(--space-5)">
                <div class="stat-card"><div class="stat-card-value">${storage.backup_count}</div><div class="stat-card-label">Total Backups</div></div>
                <div class="stat-card"><div class="stat-card-value">${usedMB} MB</div><div class="stat-card-label">Storage Used</div></div>
                <div class="stat-card"><div class="stat-card-value">${freeMB} GB</div><div class="stat-card-label">Disk Free</div></div>
            </div>

            ${backups.length > 0 ? `<div class="table-wrapper"><table class="table"><thead><tr><th>Type</th><th>Filename</th><th>Status</th><th>Size</th><th>Created</th><th style="text-align:right">Actions</th></tr></thead><tbody>
                ${backups.map(b => `<tr>
                    <td><span class="badge ${b.backup_type === 'full' ? 'badge-primary' : b.backup_type === 'website' ? 'badge-info' : 'badge-secondary'}">${b.backup_type}</span></td>
                    <td style="font-size:var(--text-xs)"><code>${b.filename || '—'}</code></td>
                    <td><span class="badge ${b.status === 'completed' ? 'badge-success' : b.status === 'in_progress' ? 'badge-warning' : b.status === 'failed' ? 'badge-danger' : 'badge-secondary'}">${b.status}</span>
                    ${b.error_message ? `<div style="font-size:var(--text-xs);color:var(--danger-400);margin-top:2px">${b.error_message}</div>` : ''}</td>
                    <td>${b.size_bytes > 0 ? formatBytes(b.size_bytes) : '—'}</td>
                    <td style="font-size:var(--text-xs);color:var(--text-tertiary)">${b.created_at ? new Date(b.created_at).toLocaleString() : '—'}</td>
                    <td><div class="table-actions">
                        ${b.status === 'completed' ? `
                            <button class="btn btn-ghost btn-sm btn-icon" onclick="downloadBackup(${b.id})" title="Download"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg></button>
                            <button class="btn btn-ghost btn-sm btn-icon" onclick="restoreBackup(${b.id})" title="Restore" style="color:var(--warning-400)"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 4v6h6M23 20v-6h-6"/><path d="M20.49 9A9 9 0 005.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 013.51 15"/></svg></button>
                        ` : ''}
                        <button class="btn btn-ghost btn-sm btn-icon" onclick="deleteBackup(${b.id})" style="color:var(--danger-400)" title="Delete"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg></button>
                    </div></td>
                </tr>`).join('')}
            </tbody></table></div>` : `<div class="card"><div class="card-body"><div class="empty-state"><div class="empty-state-icon">💾</div><h3>No backups</h3><p>Create your first backup to protect your data.</p></div></div></div>`}`;
    } catch (e) { content.innerHTML = `<div class="empty-state"><h3>Error</h3><p>${e.message}</p></div>`; }
}

function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function showCreateBackupModal() {
    openModal('Create Backup', `
        <div class="form-group"><label class="form-label">Backup Type</label>
        <select class="form-input" id="backup-type" onchange="onBackupTypeChange(this.value)">
            <option value="full">Full Server Backup</option>
            <option value="website">Website Backup</option>
            <option value="database">Database Backup</option>
        </select></div>
        <div id="backup-target-field" style="display:none"></div>
        <div class="form-group"><label class="form-label">Description (optional)</label><input type="text" class="form-input" id="backup-desc" placeholder="Before upgrade"></div>
        <div style="padding:var(--space-3);background:var(--bg-tertiary);border-radius:var(--radius-md);font-size:var(--text-xs);color:var(--text-tertiary)">
            <strong>Note:</strong> Full backups include all websites, databases, and Nginx configs. Large backups may take several minutes.
        </div>
    `, `<button class="btn btn-secondary" onclick="closeModal()">Cancel</button><button class="btn btn-primary" onclick="createBackup()">Start Backup</button>`);
}

async function onBackupTypeChange(type) {
    const field = document.getElementById('backup-target-field');
    if (type === 'website') {
        try {
            const websites = await API.get('/api/websites');
            field.style.display = 'block';
            field.innerHTML = `<div class="form-group"><label class="form-label">Select Website</label><select class="form-input" id="backup-website-id">${websites.map(w => `<option value="${w.id}">${w.domain}</option>`).join('')}</select></div>`;
        } catch (e) { field.innerHTML = '<div style="color:var(--danger-400)">Failed to load websites</div>'; }
    } else if (type === 'database') {
        try {
            const databases = await API.get('/api/databases');
            field.style.display = 'block';
            field.innerHTML = `<div class="form-group"><label class="form-label">Select Database</label><select class="form-input" id="backup-database-id">${databases.map(d => `<option value="${d.id}">${d.name}</option>`).join('')}</select></div>`;
        } catch (e) { field.innerHTML = '<div style="color:var(--danger-400)">Failed to load databases</div>'; }
    } else {
        field.style.display = 'none';
        field.innerHTML = '';
    }
}

async function createBackup() {
    const type = document.getElementById('backup-type').value;
    const body = { backup_type: type, description: document.getElementById('backup-desc').value || null };
    if (type === 'website') body.website_id = parseInt(document.getElementById('backup-website-id')?.value);
    if (type === 'database') body.database_id = parseInt(document.getElementById('backup-database-id')?.value);
    try {
        await API.post('/api/backups', body);
        closeModal(); showToast('Started', 'Backup is running in the background', 'success'); renderBackups();
    } catch (e) { showToast('Error', e.message, 'error'); }
}

function downloadBackup(id) { window.open(`/api/backups/${id}/download`, '_blank'); }

async function restoreBackup(id) { confirmModal('Restore Backup', 'Are you sure? This will overwrite existing data with the backup contents.', async () => { try { await API.post(`/api/backups/${id}/restore`); showToast('Restored', 'Backup restored successfully', 'success'); } catch (e) { showToast('Error', e.message, 'error'); } }); }

async function deleteBackup(id) { confirmModal('Delete Backup', 'Delete this backup? The backup file will also be removed from disk.', async () => { try { await API.delete(`/api/backups/${id}`); showToast('Deleted', 'Backup removed', 'success'); renderBackups(); } catch (e) { showToast('Error', e.message, 'error'); } }); }
