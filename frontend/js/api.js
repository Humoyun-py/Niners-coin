// Automatically detect if running locally or on server
const API_URL = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:5000/api'
    : '/api';

// Helper function for login URL, assuming it's defined elsewhere or needs to be added.
// For this edit, we'll define a placeholder if not present.
function getLoginUrl() {
    return '/login.html'; // Or whatever the actual login URL is
}

const api = {
    baseURL: API_URL,

    async handleResponse(response) {
        if (response.status === 401) {
            // Token expired or invalid
            localStorage.removeItem('token');
            localStorage.removeItem('user_role');
            window.location.href = getLoginUrl();
            throw new Error('Unauthorized');
        }

        if (response.status === 422) {
            // Token format compatibility issue (Subject must be a string)
            const errorData = await response.clone().json(); // Clone to not consume body for later
            if (errorData.msg && errorData.msg.includes("Subject must be a string")) {
                console.warn("Detected old token format. Forcing Re-login.");
                localStorage.clear();
                window.location.href = getLoginUrl();
                throw new Error('Session invalid (Old Token). Please Login again.');
            }
        }
        const result = await response.json();
        if (!response.ok) throw new Error(result.msg || 'Request failed');
        return result;
    },

    async post(endpoint, data) {
        try {
            const response = await fetch(`${API_URL}${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify(data)
            });
            return this.handleResponse(response);
        } catch (error) {
            console.error('API POST Error:', error);
            throw error;
        }
    },

    async get(endpoint) {
        try {
            const response = await fetch(`${API_URL}${endpoint}`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });
            return this.handleResponse(response);
        } catch (error) {
            console.error('API GET Error:', error);
            throw error;
        }
    },

    async put(endpoint, data) {
        const response = await fetch(`${API_URL}${endpoint}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: JSON.stringify(data)
        });
        const result = await response.json().catch(e => ({ msg: response.statusText }));
        if (!response.ok) {
            console.error('API PUT Error Body:', result);
            throw new Error(result.msg || 'Request failed');
        }
        return result;
    },

    async delete(endpoint) {
        const response = await fetch(`${API_URL}${endpoint}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });
        const result = await response.json().catch(e => ({ msg: response.statusText, raw_error: e.toString() }));
        if (!response.ok) {
            console.error('API DELETE Error Body:', result);
            throw new Error(result.msg || result.error || 'Request failed');
        }
        return result;
    },

    async download(endpoint, filename) {
        const response = await fetch(`${API_URL}${endpoint}`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        });
        if (!response.ok) throw new Error('Download failed');
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
    },

    async upload(endpoint, formData) {
        const response = await fetch(`${API_URL}${endpoint}`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            },
            body: formData
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.msg || 'Upload failed');
        return result;
    }
};
