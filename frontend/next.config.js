/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',  // <--- INI BIAR BISA DIUPLOAD KE S3
  images: {
    unoptimized: true,
  },
  reactStrictMode: true,
}

module.exports = nextConfig