const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const path = require('path');

const app = express();
const port = 8080;

// Serve static files from src directory (for development)
app.use(express.static(path.join(__dirname, 'public')));
app.use(express.static(path.join(__dirname, 'src')));

// API proxy to backend
app.use('/api', createProxyMiddleware({
  target: 'http://192.168.51.210:8888',
  changeOrigin: true,
  pathRewrite: {
    '^/api': ''
  }
}));

// Serve index.html for all other routes (SPA fallback)
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(port, '0.0.0.0', () => {
  console.log(`Server running at http://0.0.0.0:${port}/`);
  console.log(`Network access: http://192.168.51.210:${port}/`);
});
