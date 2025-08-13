const nextConfig = {
  webpack: (config) => {
    // Handle leaflet's issues with webpack
    config.resolve.alias = {
      ...config.resolve.alias,
      leaflet: 'leaflet/dist/leaflet.js',
    }
    return config
  },
}

module.exports = nextConfig
