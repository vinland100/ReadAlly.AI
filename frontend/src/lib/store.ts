import { create } from 'zustand';

interface AuthState {
    token: string | null;
    user: any | null;
    setToken: (token: string) => void;
    setUser: (user: any) => void;
    fetchUser: () => Promise<void>;
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
    fetchUser: async () => {
        try {
            const res = await import('./api').then(m => m.default.get('/users/me'));
            set({ user: res.data });
        } catch (e: any) {
            if (e.response?.status === 401) {
                // Token expired or invalid, fail silently and clear
                set({ token: null, user: null });
                localStorage.removeItem('token');
            } else {
                console.error("Failed to fetch user", e);
            }
        }
    },
    logout: () => {
        localStorage.removeItem('token');
        set({ token: null, user: null });
    },
}));
