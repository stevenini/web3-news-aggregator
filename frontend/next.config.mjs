/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export', // 关键：告诉 Next.js 导出静态 HTML
  images: {
    unoptimized: true, // Cloudflare Pages 不支持 Next.js 的默认图片优化服务，需要关掉
  },
};

export default nextConfig;