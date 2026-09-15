/**
 * HyperPanel — File Manager Page
 */
let currentFilePath = '';

async function renderFiles() {
    const content = document.getElementById('page-content');
    try {
        const result = await API.get(`/api/files/list?path=${encodeURIComponent(currentFilePath)}`);
        const pathSegments = currentFilePath ? currentFilePath.split('/').filter(Boolean) : [];

        content.innerHTML = `
            <div class="page-header"><div class="page-header-left"><h1>File Manager</h1><p>Browse and manage server files</p></div>
            <div class="page-header-actions">
                <button class="btn btn-secondary" onclick="showNewFolderModal()"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"/></svg> New Folder</button>
                <label class="btn btn-primary" style="cursor:pointer"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg> Upload<input type="file" style="display:none" onchange="uploadFile(this.files[0], this)"></label>
            </div></div>

            <div class="file-toolbar">
                <div class="file-path">
                    <span class="file-path-segment" onclick="navigateFiles('')">/</span>
                    ${pathSegments.map((seg, i) => `<span class="file-path-separator">/</span><span class="file-path-segment" onclick="navigateFiles('${pathSegments.slice(0, i + 1).join('/')}')">${seg}</span>`).join('')}
                </div>
                <button class="btn btn-ghost btn-sm" onclick="renderFiles()">↻ Refresh</button>
            </div>

            <div class="table-wrapper"><table class="table"><thead><tr><th>Name</th><th>Size</th><th>Permissions</th><th>Modified</th><th style="text-align:right">Actions</th></tr></thead><tbody>
                ${result.parent !== null && result.parent !== undefined ? `<tr onclick="navigateFiles('${result.parent || ''}')" style="cursor:pointer"><td><div class="file-item"><span class="file-item-icon">📁</span><span class="file-item-name">..</span></div></td><td>—</td><td>—</td><td>—</td><td></td></tr>` : ''}
                ${result.items.map(item => `
                    <tr>
                        <td>
                            <div class="file-item" ${item.type === 'directory' ? `onclick="navigateFiles('${item.path}')" style="cursor:pointer"` : `onclick="editFile('${item.path}')" style="cursor:pointer"`}>
                                <span class="file-item-icon">${item.type === 'directory' ? '📁' : getFileIcon(item.name)}</span>
                                <span class="file-item-name">${item.name}</span>
                            </div>
                        </td>
                        <td style="font-size:var(--text-xs);color:var(--text-tertiary)">${item.type === 'file' ? formatBytes(item.size) : '—'}</td>
                        <td style="font-family:var(--font-mono);font-size:var(--text-xs)">${item.permissions}</td>
                        <td style="font-size:var(--text-xs);color:var(--text-tertiary)">${new Date(item.modified).toLocaleDateString()}</td>
                        <td><div class="table-actions">
                            <button class="btn btn-ghost btn-sm btn-icon" onclick="renameFileItem('${item.path}','${item.name}')" title="Rename">✏️</button>
                            <button class="btn btn-ghost btn-sm btn-icon" onclick="deleteFileItem('${item.path}','${item.name}')" title="Delete" style="color:var(--danger-400)"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg></button>
                        </div></td>
                    </tr>
                `).join('')}
                ${result.items.length === 0 ? `<tr><td colspan="5" style="text-align:center;color:var(--text-tertiary);padding:var(--space-8)">Empty directory</td></tr>` : ''}
            </tbody></table></div>`;
    } catch (e) { content.innerHTML = `<div class="empty-state"><h3>Error</h3><p>${e.message}</p></div>`; }
}

function navigateFiles(path) { currentFilePath = path; renderFiles(); }
function getFileIcon(name) { const ext = name.split('.').pop().toLowerCase(); const icons = { php: '🐘', js: '📜', html: '🌐', css: '🎨', json: '📋', py: '🐍', md: '📝', txt: '📄', jpg: '🖼️', png: '🖼️', svg: '🖼️', zip: '📦', gz: '📦', conf: '⚙️', log: '📋' }; return icons[ext] || '📄'; }

async function editFile(path) {
    try {
        const result = await API.get(`/api/files/read?path=${encodeURIComponent(path)}`);
        const content = document.getElementById('page-content');
        content.innerHTML = `
            <div class="page-header"><div class="page-header-left"><h1>Editing: ${result.name}</h1><p>${path}</p></div>
            <div class="page-header-actions"><button class="btn btn-secondary" onclick="renderFiles()">← Back</button><button class="btn btn-primary" onclick="saveFile('${path}')"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2z"/><polyline points="17 21 17 13 7 13 7 21"/><polyline points="7 3 7 8 15 8"/></svg> Save</button></div></div>
            <div class="editor-container"><div class="editor-header"><span style="font-family:var(--font-mono);font-size:var(--text-xs);color:var(--text-tertiary)">${result.mime} · ${formatBytes(result.size)}</span></div><textarea class="editor-textarea" id="file-editor" spellcheck="false">${escapeHtml(result.content)}</textarea></div>`;
    } catch (e) { showToast('Error', e.message, 'error'); }
}

function escapeHtml(str) { return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

async function saveFile(path) {
    try {
        const content = document.getElementById('file-editor').value;
        await API.post(`/api/files/write?path=${encodeURIComponent(path)}`, content);
        showToast('Saved', 'File saved successfully', 'success');
    } catch (e) { showToast('Error', e.message, 'error'); }
}

async function uploadFile(file, inputEl) {
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    formData.append('path', currentFilePath);
    try {
        showToast('Uploading', `Uploading ${file.name}...`, 'info');
        const res = await fetch('/api/files/upload', { method: 'POST', headers: { 'Authorization': `Bearer ${API.getToken()}` }, body: formData });
        if (res.ok) {
            showToast('Uploaded', `${file.name} uploaded successfully`, 'success');
            renderFiles();
        } else {
            const err = await res.json();
            showToast('Error', err.detail || 'Failed to upload file', 'error');
        }
    } catch (e) {
        showToast('Error', e.message, 'error');
    } finally {
        if (inputEl) inputEl.value = '';
    }
}


function showNewFolderModal() {
    openModal('New Folder', `<div class="form-group"><label class="form-label">Folder Name</label><input type="text" class="form-input" id="new-folder-name" placeholder="my-folder"></div>`,
    `<button class="btn btn-secondary" onclick="closeModal()">Cancel</button><button class="btn btn-primary" onclick="createFolder()">Create</button>`);
}

async function createFolder() {
    const name = document.getElementById('new-folder-name').value;
    try { await API.post(`/api/files/mkdir?path=${encodeURIComponent(currentFilePath ? currentFilePath + '/' + name : name)}`); closeModal(); showToast('Created', 'Folder created', 'success'); renderFiles(); } catch (e) { showToast('Error', e.message, 'error'); }
}

function renameFileItem(path, oldName) {
    openModal('Rename', `<div class="form-group"><label class="form-label">New Name</label><input type="text" class="form-input" id="rename-input" value="${oldName}"></div>`,
    `<button class="btn btn-secondary" onclick="closeModal()">Cancel</button><button class="btn btn-primary" onclick="doRename('${path}')">Rename</button>`);
}

async function doRename(path) { try { await API.post(`/api/files/rename?path=${encodeURIComponent(path)}&new_name=${encodeURIComponent(document.getElementById('rename-input').value)}`); closeModal(); renderFiles(); } catch (e) { showToast('Error', e.message, 'error'); } }

function deleteFileItem(path, name) { confirmModal('Delete', `Delete "${name}"?`, async () => { try { await API.delete(`/api/files/delete?path=${encodeURIComponent(path)}`); showToast('Deleted', `${name} deleted`, 'success'); renderFiles(); } catch (e) { showToast('Error', e.message, 'error'); } }); }
