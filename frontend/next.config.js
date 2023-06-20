const API_URL = 'http://127.0.0.1:20110';
module.exports = {
  reactStrictMode: false,
  async rewrites() {
    return [
      {
        source: '/apis/:path*',
        destination: `${API_URL}/apis/:path*` // Proxy to Backend
      }
    ]
  }
};
