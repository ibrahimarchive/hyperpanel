/**
 * HyperPanel — Cron Jobs Page
 */
async function renderCron() {
    const content = document.getElementById('page-content');
    try {
        const jobs = await API.get('/api/cron');
        const presets = await API.get('/api/cron/presets');

        content.innerHTML = `
            <div class="page-header"><div class="page-header-left"><h1>Cron Jobs</h1><p>Schedule recurring tasks</p></div>
            <div class="page-header-actions"><button class="btn btn-primary" onclick="showCreateCronModal()"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg> New Cron Job</button></div></div>

            ${jobs.length > 0 ? `<div class="table-wrapper"><table class="table"><thead><tr><th>Schedule</th><th>Description</th><th>Command</th><th>Last Run</th><th>Status</th><th>Enabled</th><th style="text-align:right">Actions</th></tr></thead><tbody>
                ${jobs.map(j => `<tr>
                    <td><code style="font-size:var(--text-xs);background:var(--bg-tertiary);padding:2px 8px;border-radius:4px">${j.schedule}</code></td>
                    <td>${j.description || '—'}</td>
                    <td style="max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap"><code style="font-size:var(--text-xs)">${j.command}</code></td>
                    <td style="font-size:var(--text-xs);color:var(--text-tertiary)">${j.last_run ? new Date(j.last_run).toLocaleString() : 'Never'}</td>
                    <td>${j.last_status ? `<span class="badge ${j.last_status === 'success' ? 'badge-success' : 'badge-danger'}">${j.last_status}</span>` : '<span class="badge badge-secondary">—</span>'}</td>
                    <td><label class="toggle"><input type="checkbox" ${j.enabled ? 'checked' : ''} onchange="toggleCronJob(${j.id})"><span class="toggle-slider"></span></label></td>
                    <td><div class="table-actions">
                        <button class="btn btn-ghost btn-sm btn-icon" onclick="showEditCronModal(${j.id}, '${j.schedule}', \`${j.command.replace(/`/g, '\\`')}\`, '${j.description || ''}')" title="Edit"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/></svg></button>
                        <button class="btn btn-ghost btn-sm btn-icon" onclick="deleteCronJob(${j.id})" style="color:var(--danger-400)" title="Delete"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg></button>
                    </div></td>
                </tr>`).join('')}
            </tbody></table></div>` : `<div class="card"><div class="card-body"><div class="empty-state"><div class="empty-state-icon">⏰</div><h3>No cron jobs</h3><p>Schedule your first recurring task.</p></div></div></div>`}`;

        // Store presets globally for modal
        window._cronPresets = presets;
    } catch (e) { content.innerHTML = `<div class="empty-state"><h3>Error</h3><p>${e.message}</p></div>`; }
}

function showCreateCronModal() {
    const presets = window._cronPresets || [];
    openModal('Create Cron Job', `
        <div class="form-group"><label class="form-label">Schedule Preset</label>
        <select class="form-input" id="cron-preset" onchange="applyCronPreset(this.value)">
            <option value="">Custom</option>
            ${presets.map(p => `<option value="${p.schedule}">${p.description} (${p.schedule})</option>`).join('')}
        </select></div>
        <div class="form-group"><label class="form-label">Schedule (cron expression)</label><input type="text" class="form-input" id="cron-schedule" placeholder="* * * * *">
        <div style="font-size:var(--text-xs);color:var(--text-tertiary);margin-top:4px">Format: minute hour day month weekday</div></div>
        <div class="form-group"><label class="form-label">Command</label><input type="text" class="form-input" id="cron-command" placeholder="/usr/bin/php /var/www/site/artisan schedule:run"></div>
        <div class="form-group"><label class="form-label">Description (optional)</label><input type="text" class="form-input" id="cron-desc" placeholder="Laravel scheduler"></div>
    `, `<button class="btn btn-secondary" onclick="closeModal()">Cancel</button><button class="btn btn-primary" onclick="createCronJob()">Create</button>`);
}

function applyCronPreset(value) { if (value) document.getElementById('cron-schedule').value = value; }

function showEditCronModal(id, schedule, command, description) {
    openModal('Edit Cron Job', `
        <div class="form-group"><label class="form-label">Schedule</label><input type="text" class="form-input" id="cron-edit-schedule" value="${schedule}"></div>
        <div class="form-group"><label class="form-label">Command</label><input type="text" class="form-input" id="cron-edit-command" value="${command}"></div>
        <div class="form-group"><label class="form-label">Description</label><input type="text" class="form-input" id="cron-edit-desc" value="${description}"></div>
    `, `<button class="btn btn-secondary" onclick="closeModal()">Cancel</button><button class="btn btn-primary" onclick="updateCronJob(${id})">Save</button>`);
}

async function createCronJob() {
    try {
        await API.post('/api/cron', { schedule: document.getElementById('cron-schedule').value, command: document.getElementById('cron-command').value, description: document.getElementById('cron-desc').value || null });
        closeModal(); showToast('Created', 'Cron job created', 'success'); renderCron();
    } catch (e) { showToast('Error', e.message, 'error'); }
}

async function updateCronJob(id) {
    try {
        await API.put(`/api/cron/${id}`, { schedule: document.getElementById('cron-edit-schedule').value, command: document.getElementById('cron-edit-command').value, description: document.getElementById('cron-edit-desc').value || null });
        closeModal(); showToast('Updated', 'Cron job updated', 'success'); renderCron();
    } catch (e) { showToast('Error', e.message, 'error'); }
}

async function deleteCronJob(id) { confirmModal('Delete Cron Job', 'Are you sure? This will also remove it from the system crontab.', async () => { try { await API.delete(`/api/cron/${id}`); showToast('Deleted', 'Cron job removed', 'success'); renderCron(); } catch (e) { showToast('Error', e.message, 'error'); } }); }

async function toggleCronJob(id) { try { await API.post(`/api/cron/${id}/toggle`); showToast('Success', 'Cron job toggled', 'success'); renderCron(); } catch (e) { showToast('Error', e.message, 'error'); } }
