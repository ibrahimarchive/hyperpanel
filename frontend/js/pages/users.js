/**
 * HyperPanel — Users Page
 */
async function renderUsers() {
    const content = document.getElementById('page-content');
    if (!isAdmin()) { content.innerHTML = `<div class="card"><div class="card-body"><div class="empty-state"><h3>Access Denied</h3><p>Only administrators can manage users.</p></div></div></div>`; return; }
    try {
        const users = await API.get('/api/users');
        content.innerHTML = `
            <div class="page-header"><div class="page-header-left"><h1>Users</h1><p>Manage panel user accounts</p></div>
            <div class="page-header-actions"><button class="btn btn-primary" onclick="showCreateUserModal()"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M5 12h14"/></svg> Add User</button></div></div>
            <div class="table-wrapper"><table class="table"><thead><tr><th>User</th><th>Email</th><th>Role</th><th>Status</th><th>Websites</th><th>Last Login</th><th style="text-align:right">Actions</th></tr></thead><tbody>
                ${users.map(u => `<tr><td><div style="display:flex;align-items:center;gap:var(--space-3)"><div class="topbar-avatar" style="width:28px;height:28px;font-size:var(--text-xs)">${(u.username || 'U')[0].toUpperCase()}</div><div><div style="font-weight:var(--font-medium)">${u.username}</div>${u.full_name ? `<div style="font-size:var(--text-xs);color:var(--text-tertiary)">${u.full_name}</div>` : ''}</div></div></td><td>${u.email}</td><td><span class="badge ${u.role === 'admin' ? 'badge-danger' : u.role === 'reseller' ? 'badge-warning' : 'badge-info'}">${u.role}</span></td><td><span class="badge ${u.is_active ? 'badge-success' : 'badge-danger'}">${u.is_active ? 'Active' : 'Disabled'}</span></td><td>${u.max_websites}</td><td style="font-size:var(--text-xs);color:var(--text-tertiary)">${u.last_login ? timeAgo(u.last_login) : 'Never'}</td><td><div class="table-actions">${u.role !== 'admin' ? `<button class="btn btn-ghost btn-sm btn-icon" onclick="deleteUser(${u.id},'${u.username}')" style="color:var(--danger-400)"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"/></svg></button>` : ''}</div></td></tr>`).join('')}
            </tbody></table></div>`;
    } catch (e) { content.innerHTML = `<div class="empty-state"><h3>Error</h3><p>${e.message}</p></div>`; }
}

function showCreateUserModal() {
    openModal('Create User', `
        <div class="form-group"><label class="form-label">Username</label><input type="text" class="form-input" id="new-user-name" placeholder="johndoe"></div>
        <div class="form-group"><label class="form-label">Email</label><input type="email" class="form-input" id="new-user-email" placeholder="john@example.com"></div>
        <div class="form-group"><label class="form-label">Password</label><input type="password" class="form-input" id="new-user-pass" placeholder="Strong password"></div>
        <div class="form-group"><label class="form-label">Role</label><select class="form-input" id="new-user-role"><option value="user">User</option><option value="reseller">Reseller</option><option value="admin">Admin</option></select></div>
        <div class="form-group"><label class="form-label">Max Websites</label><input type="number" class="form-input" id="new-user-sites" value="10"></div>
    `, `<button class="btn btn-secondary" onclick="closeModal()">Cancel</button><button class="btn btn-primary" onclick="createUser()">Create User</button>`);
}

async function createUser() {
    try {
        await API.post('/api/users', { username: document.getElementById('new-user-name').value, email: document.getElementById('new-user-email').value, password: document.getElementById('new-user-pass').value, role: document.getElementById('new-user-role').value, max_websites: parseInt(document.getElementById('new-user-sites').value) });
        closeModal(); showToast('Created', 'User created successfully', 'success'); renderUsers();
    } catch (e) { showToast('Error', e.message, 'error'); }
}

async function deleteUser(id, username) {
    confirmModal('Delete User', `Delete user "${username}"? This cannot be undone.`, async () => {
        try { await API.delete(`/api/users/${id}`); showToast('Deleted', `User ${username} removed`, 'success'); renderUsers(); } catch (e) { showToast('Error', e.message, 'error'); }
    });
}
