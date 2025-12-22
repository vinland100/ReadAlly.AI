/** @type {import('next').NextConfig} */
const nextConfig = {
    output: "standalone",
    serverActions: {
        allowedOrigins: [
            //开发环境保持为空，docker compose部署/生产环境使用环境变量灵活扩展
            ...(process.env.ALLOWED_ORIGINS ? process.env.ALLOWED_ORIGINS.split(",") : [])
        ],
    },
    generateBuildId: async () => {
        // Use a consistent build ID (you could also use a git commit hash here)
        return 'readally-build-id'
    },
    async rewrites() {
        // 优先使用环境变量，其次尝试 Docker 内部服务名，最后回退到 localhost
        const backendUrl = process.env.INTERNAL_API_URL || 'http://readally-backend:8000';
        return [
            {
                source: '/api/:path*',
                destination: `${backendUrl}/api/:path*`,
            },
            {
                source: '/token',
                destination: `${backendUrl}/token`,
            },
            {
                source: '/register',
                destination: `${backendUrl}/register`,
            },
            {
                source: '/users/:path*',
                destination: `${backendUrl}/users/:path*`,
            },
            {
                source: '/static/:path*',
                destination: `${backendUrl}/static/:path*`,
            },
        ]
    },
};

module.exports = nextConfig;
