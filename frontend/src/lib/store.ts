import { create } from 'zustand'

interface User {
  id:         string
  email:      string
  role:       string
  full_name:  string
  department?: string
}

interface AuthStore {
  user:    User | null
  setUser: (user: User | null) => void
}

export const useAuthStore = create<AuthStore>((set) => ({
  user:    null,
  setUser: (user) => set({ user }),
}))
