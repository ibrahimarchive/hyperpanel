/**
 * HyperPanel — API Client
 * Centralized fetch wrapper with JWT auth and error handling.
 */

const API = {
    baseUrl: '',

    getToken() {
        return localStorage.getItem('hyperpanel-token');
    },

    async request(endpoint, options = {}) {
        const url = `${this.baseUrl}${endpoint}`;
        const token = this.getToken();

        const headers = {
            'Content-Type': 'application/json',
            ...(options.headers || {}),
        };

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        try {
            const res = await fetch(url, {
                ...options,
                headers,
            });

            // Handle 401 — token expired
            if (res.status === 401) {
                const refreshed = await this.refreshToken();
                if (refreshed) {
                    headers['Authorization'] = `Bearer ${this.getToken()}`;
                    const retry = await fetch(url, { ...options, headers });
                    return this.handleResponse(retry);
                } else {
                    logout();
                    return null;
                }
            }

            return this.handleResponse(res);
        } catch (err) {
            console.error('API Error:', err);
            showToast('Connection Error', 'Could not reach the server', 'error');
            throw err;
        }
    },

    async handleResponse(res) {
        const data = await res.json().catch(() => null);

        if (!res.ok) {
            const message = data?.detail || `Error ${res.status}`;
            throw new Error(message);
        }

        return data;
    },

    async refreshToken() {
        const refreshToken = localStorage.getItem('hyperpanel-refresh');
        if (!refreshToken) return false;

        try {
            const res = await fetch('/api/auth/refresh', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh_token: refreshToken }),
            });

            if (res.ok) {
                const data = await res.json();
                localStorage.setItem('hyperpanel-token', data.access_token);
                localStorage.setItem('hyperpanel-refresh', data.refresh_token);
                return true;
            }
        } catch (e) {
            console.error('Token refresh failed:', e);
        }

        return false;
    },

    get(endpoint) {
        return this.request(endpoint, { method: 'GET' });
    },

    post(endpoint, body) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(body),
        });
    },

    put(endpoint, body) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(body),
        });
    },

    delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    },
};
