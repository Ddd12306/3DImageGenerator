import { defineStore } from 'pinia'
import { api, type User } from '../api'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null as User | null,
    checked: false
  }),
  actions: {
    async load() {
      try {
        const result = await api.me()
        this.user = result.user
      } catch {
        this.user = null
      } finally {
        this.checked = true
      }
    },
    async login(username: string, password: string) {
      const result = await api.login(username, password)
      this.user = result.user
    },
    async register(username: string, password: string) {
      const result = await api.register(username, password)
      this.user = result.user
    },
    async logout() {
      await api.logout()
      this.user = null
    }
  }
})
