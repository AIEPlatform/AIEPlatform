module.exports = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: '/apis/:path*',
        destination: 'localhost:20110/apis/:path*' // Proxy to Backend
      }
    ]
  }
};
