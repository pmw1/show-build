const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  transpileDependencies: true,
  
  devServer: {
    host: '0.0.0.0', // Bind to all interfaces
    port: 8080,
    allowedHosts: 'all',
    proxy: {
      '/api': {
        target: 'http://192.168.51.210:8888',
        changeOrigin: true,
        secure: false,
        pathRewrite: {
          '^/api': ''
        }
      }
    }
  }
})
