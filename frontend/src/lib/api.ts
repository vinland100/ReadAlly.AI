import axios from 'axios';

const api = axios.create({
    // 逻辑：
    // 1. 如果环境变量有值，直接用 (本地开发时设置为 http://localhost:8000)
    // 2. 如果是生产环境，且没设变量，则通过判断 window 是否存在来决定
    //    - 浏览器端：直接用 '/'，会自动拼接当前域名
    //    - 服务端 (SSR)：必须写完整地址访问本地后端
    baseURL: process.env.NEXT_PUBLIC_API_URL || 
             (typeof window === 'undefined' ? 'http://localhost:8000' : '/'),
});

api.interceptors.request.use((config) => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

export default api;
