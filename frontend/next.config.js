/** @type {import('next').NextConfig} */
const nextConfig = {
    output: "standalone",
    experimental: {
        serverActions: {
            allowedOrigins: [
                "localhost:3000",
                "127.0.0.1:3000",
                "0.0.0.0:3000",
                "vinland100.tech",
                "www.vinland100.tech",
                ...(process.env.ALLOWED_ORIGINS ? process.env.ALLOWED_ORIGINS.split(",") : [])
            ],
        },
    },
};

module.exports = nextConfig;
