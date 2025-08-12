const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  transpileDependencies: true,
  
  devServer: {
    host: '0.0.0.0',
    port: 8080,
    allowedHosts: 'all',
    proxy: {
      '/api': {
        target: 'http://192.168.51.210:8888',
        changeOrigin: true,
        secure: false
      },
      '/health': {
        target: 'http://192.168.51.210:8888',
        changeOrigin: true,
        secure: false
      }
    }
  }
});
