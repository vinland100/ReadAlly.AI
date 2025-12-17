import { create } from 'zustand';

interface AuthState {
    token: string | null;
    user: any | null;
    setToken: (token: string) => void;
    setUser: (user: any) => void;
    logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
    token: typeof window !== 'undefined' ? localStorage.getItem('token') : null,
    user: null,
    setToken: (token) => {
        localStorage.setItem('token', token);
        set({ token });
    },
    setUser: (user) => set({ user }),
    logout: () => {
        localStorage.removeItem('token');
        set({ token: null, user: null });
    },
}));
