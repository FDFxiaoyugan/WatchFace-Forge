/** @type {import('next').NextConfig} */
const apiTarget = process.env.API_PROXY_TARGET || 'http://localhost:8000';

const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        // 容器内通过 compose 服务名访问 API (API_PROXY_TARGET=http://api:8000);
        // 本地开发默认 localhost:8000。
        destination: `${apiTarget}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
