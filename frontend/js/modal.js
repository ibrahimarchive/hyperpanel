/**
 * HyperPanel — Modal Manager
 */

function openModal(title, bodyHTML, footerHTML = '') {
    const overlay = document.getElementById('modal-overlay');
    const titleEl = document.getElementById('modal-title');
    const bodyEl = document.getElementById('modal-body');
    const footerEl = document.getElementById('modal-footer');

    titleEl.textContent = title;
    bodyEl.innerHTML = bodyHTML;
    footerEl.innerHTML = footerHTML;

    overlay.classList.add('active');

    // Close on overlay click
    overlay.onclick = (e) => {
        if (e.target === overlay) closeModal();
    };

    // Close on Escape
    document.addEventListener('keydown', handleModalEscape);
}

function closeModal() {
    const overlay = document.getElementById('modal-overlay');
    overlay.classList.remove('active');
    document.removeEventListener('keydown', handleModalEscape);
}

function handleModalEscape(e) {
    if (e.key === 'Escape') closeModal();
}

function confirmModal(title, message, onConfirm, type = 'danger') {
    const safeMsg = typeof escapeHtml === 'function' ? escapeHtml(message) : message;
    const safeTitle = typeof escapeHtml === 'function' ? escapeHtml(title) : title;
    const body = `<p style="color: var(--text-secondary); font-size: var(--text-sm);">${safeMsg}</p>`;
    const footer = `
        <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
        <button class="btn btn-${type}" id="confirm-action-btn">${safeTitle}</button>
    `;

    openModal(title, body, footer);

    document.getElementById('confirm-action-btn').onclick = () => {
        closeModal();
        onConfirm();
    };
}
