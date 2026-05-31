import { defineStore } from 'pinia';
import { api } from '../api';
export const useAuthStore = defineStore('auth', {
    state: () => ({
        user: null,
        checked: false
    }),
    actions: {
        async load() {
            try {
                const result = await api.me();
                this.user = result.user;
            }
            catch {
                this.user = null;
            }
            finally {
                this.checked = true;
            }
        },
        async login(username, password) {
            const result = await api.login(username, password);
            this.user = result.user;
        },
        async register(username, password) {
            const result = await api.register(username, password);
            this.user = result.user;
        },
        async logout() {
            await api.logout();
            this.user = null;
        }
    }
});
//# sourceMappingURL=auth.js.map