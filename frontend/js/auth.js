/**
 * HyperPanel — Auth Module
 * Handles authentication state and user profile.
 */

let currentUser = null;

async function checkAuth() {
    const token = localStorage.getItem('hyperpanel-token');
    if (!token) {
        window.location.href = '/login';
        return false;
    }

    try {
        currentUser = await API.get('/api/auth/me');
        updateUserUI();
        return true;
    } catch (e) {
        window.location.href = '/login';
        return false;
    }
}

function updateUserUI() {
    if (!currentUser) return;

    const nameEl = document.getElementById('user-display-name');
    const roleEl = document.getElementById('user-display-role');
    const avatarEl = document.getElementById('user-avatar');

    if (nameEl) nameEl.textContent = currentUser.full_name || currentUser.username;
    if (roleEl) roleEl.textContent = currentUser.role.charAt(0).toUpperCase() + currentUser.role.slice(1);
    if (avatarEl) avatarEl.textContent = (currentUser.username || 'A')[0].toUpperCase();
}

function logout() {
    localStorage.removeItem('hyperpanel-token');
    localStorage.removeItem('hyperpanel-refresh');
    currentUser = null;
    window.location.href = '/login';
}

function isAdmin() {
    return currentUser && currentUser.role === 'admin';
}
