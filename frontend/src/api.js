async function request(url, options = {}) {
    const response = await fetch(url, {
        credentials: 'include',
        headers: {
            ...(options.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }),
            ...(options.headers || {})
        },
        ...options
    });
    if (!response.ok) {
        const payload = await response.json().catch(() => ({}));
        throw new Error(payload.detail || `请求失败 (${response.status})`);
    }
    return response.json();
}
export const api = {
    getPresets: () => request('/api/presets'),
    me: () => request('/api/me'),
    register: (username, password) => request('/api/auth/register', {
        method: 'POST',
        body: JSON.stringify({ username, password })
    }),
    login: (username, password) => request('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({ username, password })
    }),
    logout: () => request('/api/auth/logout', { method: 'POST' }),
    generateText: (presetId, prompt, fields) => request('/api/generate/text', {
        method: 'POST',
        body: JSON.stringify({ preset_id: presetId, prompt, fields })
    }),
    generateImage: (presetId, prompt, fields, file) => {
        const form = new FormData();
        form.append('file', file);
        form.append('preset_id', presetId);
        form.append('prompt', prompt);
        form.append('fields_json', JSON.stringify(fields));
        return request('/api/generate/image', {
            method: 'POST',
            body: form
        });
    },
    getTasks: () => request('/api/tasks'),
    deleteTask: (taskId) => request(`/api/tasks/${taskId}`, { method: 'DELETE' })
};
//# sourceMappingURL=api.js.map