/** @type {import('next').NextConfig} */
const nextConfig = {
    output: "standalone",
    serverActions: {
        allowedOrigins: [
            //开发环境保持为空，docker compose部署/生产环境使用环境变量灵活扩展
            ...(process.env.ALLOWED_ORIGINS ? process.env.ALLOWED_ORIGINS.split(",") : [])
        ],
    }
};

module.exports = nextConfig;
