import { create } from 'zustand'

interface User {
  id:         string
  email:      string
  role:       string
  full_name:  string
  department?: string
  /** 初期パスワード（生年月日）のまま。true の間はパスワード変更画面を出す */
  must_change_password?: boolean
}

interface AuthStore {
  user:    User | null
  setUser: (user: User | null) => void
}

export const useAuthStore = create<AuthStore>((set) => ({
  user:    null,
  setUser: (user) => set({ user }),
}))
