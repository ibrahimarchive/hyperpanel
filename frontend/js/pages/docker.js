/**
 * HyperPanel — Docker Management Page
 */
let _dockerTab = 'containers';

async function renderDocker() {
    const content = document.getElementById('page-content');
    try {
        const status = await API.get('/api/docker/status');

        if (!status.installed) {
            content.innerHTML = `
                <div class="page-header"><div class="page-header-left"><h1>Docker</h1><p>Container management</p></div></div>
                <div class="card"><div class="card-body" style="text-align:center;padding:var(--space-8)">
                    <div style="font-size:48px;margin-bottom:var(--space-4)">🐳</div>
                    <h2 style="margin-bottom:var(--space-2)">Docker Not Installed</h2>
                    <p style="color:var(--text-tertiary);margin-bottom:var(--space-5);max-width:400px;margin-left:auto;margin-right:auto">Docker Engine is not installed on this server. Install it to manage containers, images, and deploy applications.</p>
                    <button class="btn btn-primary" onclick="installDocker()"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg> Install Docker Engine</button>
                    <div style="font-size:var(--text-xs);color:var(--text-tertiary);margin-top:var(--space-3)">This will install Docker CE from the official repository.</div>
                </div></div>`;
            return;
        }

        const containers = _dockerTab === 'containers' ? await API.get('/api/docker/containers') : [];
        const images = _dockerTab === 'images' ? await API.get('/api/docker/images') : [];

        content.innerHTML = `
            <div class="page-header"><div class="page-header-left"><h1>Docker</h1><p>${status.version || 'Container management'}</p></div>
            <div class="page-header-actions">
                ${_dockerTab === 'containers' ? '<button class="btn btn-primary" onclick="showCreateContainerModal()"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg> New Container</button>' : '<button class="btn btn-primary" onclick="showPullImageModal()"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg> Pull Image</button>'}
                <button class="btn btn-ghost btn-sm" onclick="uninstallDocker()" style="color:var(--danger-400)" title="Uninstall Docker Engine"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg> Uninstall</button>
            </div></div>

            <div class="grid grid-3" style="margin-bottom:var(--space-5)">
                <div class="stat-card"><div class="stat-card-value">${status.containers_running}</div><div class="stat-card-label">Running</div></div>
                <div class="stat-card"><div class="stat-card-value">${status.containers_total}</div><div class="stat-card-label">Total Containers</div></div>
                <div class="stat-card"><div class="stat-card-value">${status.images_count}</div><div class="stat-card-label">Images</div></div>
            </div>

            <div style="display:flex;gap:var(--space-2);margin-bottom:var(--space-4)">
                <button class="btn ${_dockerTab === 'containers' ? 'btn-primary' : 'btn-ghost'} btn-sm" onclick="switchDockerTab('containers')">Containers</button>
                <button class="btn ${_dockerTab === 'images' ? 'btn-primary' : 'btn-ghost'} btn-sm" onclick="switchDockerTab('images')">Images</button>
            </div>

            ${_dockerTab === 'containers' ? renderContainersTable(containers) : renderImagesTable(images)}`;
    } catch (e) { content.innerHTML = `<div class="empty-state"><h3>Error</h3><p>${e.message}</p></div>`; }
}

function renderContainersTable(containers) {
    if (!containers.length) return `<div class="card"><div class="card-body"><div class="empty-state"><div class="empty-state-icon">🐳</div><h3>No containers</h3><p>Create your first container.</p></div></div></div>`;
    return `<div class="table-wrapper"><table class="table"><thead><tr><th>Name</th><th>Image</th><th>Status</th><th>Ports</th><th style="text-align:right">Actions</th></tr></thead><tbody>
        ${containers.map(c => `<tr>
            <td style="font-weight:var(--font-medium)">${c.name}</td>
            <td><code style="font-size:var(--text-xs)">${c.image}</code></td>
            <td><span class="badge ${c.state === 'running' ? 'badge-success' : c.state === 'exited' ? 'badge-danger' : 'badge-warning'}">${c.state}</span><div style="font-size:var(--text-xs);color:var(--text-tertiary)">${c.status}</div></td>
            <td style="font-size:var(--text-xs)">${c.ports || '—'}</td>
            <td><div class="table-actions">
                ${c.state !== 'running' ? `<button class="btn btn-ghost btn-sm btn-icon" onclick="dockerAction('${c.id}','start')" title="Start" style="color:var(--success-400)"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg></button>` : `<button class="btn btn-ghost btn-sm btn-icon" onclick="dockerAction('${c.id}','stop')" title="Stop" style="color:var(--warning-400)"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></svg></button><button class="btn btn-ghost btn-sm btn-icon" onclick="dockerAction('${c.id}','restart')" title="Restart"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 4v6h6M23 20v-6h-6"/><path d="M20.49 9A9 9 0 005.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 013.51 15"/></svg></button>`}
                <button class="btn btn-ghost btn-sm btn-icon" onclick="showContainerLogs('${c.id}','${c.name}')" title="Logs"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><path d="M14 2v6h6M16 13H8M16 17H8M10 9H8"/></svg></button>
                <button class="btn btn-ghost btn-sm btn-icon" onclick="dockerAction('${c.id}','remove')" title="Remove" style="color:var(--danger-400)"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg></button>
            </div></td></tr>`).join('')}
    </tbody></table></div>`;
}

function renderImagesTable(images) {
    if (!images.length) return `<div class="card"><div class="card-body"><div class="empty-state"><div class="empty-state-icon">📦</div><h3>No images</h3><p>Pull your first Docker image.</p></div></div></div>`;
    return `<div class="table-wrapper"><table class="table"><thead><tr><th>Repository</th><th>Tag</th><th>ID</th><th>Size</th><th style="text-align:right">Actions</th></tr></thead><tbody>
        ${images.map(i => `<tr>
            <td style="font-weight:var(--font-medium)">${i.repository}</td>
            <td><span class="badge badge-secondary">${i.tag}</span></td>
            <td><code style="font-size:var(--text-xs)">${i.id}</code></td>
            <td>${i.size}</td>
            <td><div class="table-actions"><button class="btn btn-ghost btn-sm btn-icon" onclick="removeImage('${i.id}')" style="color:var(--danger-400)" title="Remove"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg></button></div></td>
        </tr>`).join('')}
    </tbody></table></div>`;
}

function switchDockerTab(tab) { _dockerTab = tab; renderDocker(); }

async function installDocker() {
    if (!confirm('Install Docker Engine? This may take a few minutes.')) return;
    showToast('Installing', 'Docker installation started...', 'info');
    try {
        await API.post('/api/docker/install');
        showToast('Installed', 'Docker Engine installed successfully', 'success');
        renderDocker();
    } catch (e) { showToast('Error', e.message, 'error'); }
}

function showCreateContainerModal() {
    openModal('Create Container', `
        <div class="form-group"><label class="form-label">Image</label><input type="text" class="form-input" id="docker-image" placeholder="nginx:latest"></div>
        <div class="form-group"><label class="form-label">Container Name</label><input type="text" class="form-input" id="docker-name" placeholder="my-nginx"></div>
        <div class="form-group"><label class="form-label">Ports (comma-separated)</label><input type="text" class="form-input" id="docker-ports" placeholder="80:80, 443:443"></div>
        <div class="form-group"><label class="form-label">Volumes (comma-separated)</label><input type="text" class="form-input" id="docker-volumes" placeholder="/host/path:/container/path"></div>
        <div class="form-group"><label class="form-label">Environment Variables (comma-separated)</label><input type="text" class="form-input" id="docker-env" placeholder="KEY=value, KEY2=value2"></div>
        <div class="form-group"><label class="form-label">Restart Policy</label><select class="form-input" id="docker-restart"><option value="unless-stopped">Unless Stopped</option><option value="always">Always</option><option value="on-failure">On Failure</option><option value="no">No</option></select></div>
    `, `<button class="btn btn-secondary" onclick="closeModal()">Cancel</button><button class="btn btn-primary" onclick="createContainer()">Create & Start</button>`);
}

async function createContainer() {
    try {
        const params = new URLSearchParams({
            image: document.getElementById('docker-image').value,
            name: document.getElementById('docker-name').value || '',
            ports: document.getElementById('docker-ports').value || '',
            volumes: document.getElementById('docker-volumes').value || '',
            env_vars: document.getElementById('docker-env').value || '',
            restart_policy: document.getElementById('docker-restart').value,
        });
        await API.post(`/api/docker/containers?${params}`);
        closeModal(); showToast('Created', 'Container created and started', 'success'); renderDocker();
    } catch (e) { showToast('Error', e.message, 'error'); }
}

function showPullImageModal() {
    openModal('Pull Image', `<div class="form-group"><label class="form-label">Image Name</label><input type="text" class="form-input" id="docker-pull-image" placeholder="nginx:latest or redis:alpine"></div>`,
    `<button class="btn btn-secondary" onclick="closeModal()">Cancel</button><button class="btn btn-primary" onclick="pullImage()">Pull</button>`);
}

async function pullImage() {
    const image = document.getElementById('docker-pull-image').value;
    if (!image) return;
    closeModal(); showToast('Pulling', `Pulling ${image}...`, 'info');
    try { await API.post(`/api/docker/images/pull?image=${encodeURIComponent(image)}`); showToast('Pulled', `Image ${image} pulled`, 'success'); renderDocker(); } catch (e) { showToast('Error', e.message, 'error'); }
}

async function dockerAction(id, action) {
    if (action === 'remove' && !confirm('Remove this container?')) return;
    try { await API.post(`/api/docker/containers/${id}/${action}`); showToast('Success', `Container ${action}ed`, 'success'); renderDocker(); } catch (e) { showToast('Error', e.message, 'error'); }
}

async function showContainerLogs(id, name) {
    try {
        const data = await API.get(`/api/docker/containers/${id}/logs?tail=200`);
        openModal(`Logs — ${name}`, `<pre style="margin:0;padding:var(--space-3);background:var(--bg-primary);color:var(--text-secondary);font-family:'JetBrains Mono',monospace;font-size:11px;line-height:1.5;max-height:500px;overflow:auto;white-space:pre-wrap;word-break:break-all;border-radius:var(--radius-md)">${data.logs || 'No logs'}</pre>`,
        `<button class="btn btn-secondary" onclick="closeModal()">Close</button>`);
    } catch (e) { showToast('Error', e.message, 'error'); }
}

async function removeImage(id) { if (!confirm('Remove this image?')) return; try { await API.delete(`/api/docker/images/${id}`); showToast('Removed', 'Image removed', 'success'); renderDocker(); } catch (e) { showToast('Error', e.message, 'error'); } }

async function uninstallDocker() {
    confirmModal(
        'Uninstall Docker Engine',
        'Are you sure you want to uninstall Docker Engine? All containers will be stopped and Docker packages purged to keep the server minimal. Existing website files and databases will not be touched.',
        async () => {
            showToast('Uninstalling', 'Purging Docker Engine...', 'info');
            try {
                await API.post('/api/docker/uninstall');
                showToast('Success', 'Docker Engine uninstalled successfully', 'success');
                renderDocker();
            } catch (e) {
                showToast('Error', e.message, 'error');
            }
        },
        'danger'
    );
}

