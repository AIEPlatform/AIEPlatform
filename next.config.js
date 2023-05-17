module.exports = {
  reactStrictMode: true,
  async rewrites() {
    return [
      {
        source: '/apis/:path*',
        destination: 'http://127.0.0.1:20110/apis/:path*' // Proxy to Backend
      }
    ]
  }
};
