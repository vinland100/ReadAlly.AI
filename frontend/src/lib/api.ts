import axios from 'axios';

const getBaseUrl = () => {
    if (typeof window === 'undefined') {
        // Server-side (SSR)
        // 1. Try internal docker network URL first
        if (process.env.INTERNAL_API_URL) return process.env.INTERNAL_API_URL;
        // 2. Fallback to public URL (for manual dev) or localhost default
        return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    } else {
        // Client-side (Browser)
        // 1. Use public API URL if set
        return process.env.NEXT_PUBLIC_API_URL || '/';
    }
};

const api = axios.create({
    baseURL: getBaseUrl(),
});

api.interceptors.request.use((config) => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

export default api;
