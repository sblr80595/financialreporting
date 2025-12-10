const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  // Determine backend URL based on environment
  // In Docker: use 'backend' hostname
  // Locally: use 'localhost'
  const target = process.env.PROXY_TARGET || 'http://localhost:8001';
  
  console.log(`[Proxy] Proxying API requests to: ${target}`);
  
  app.use(
    '/api',
    createProxyMiddleware({
      target: target,
      changeOrigin: true,
      logLevel: 'debug',
      onError: (err, req, res) => {
        console.error('[Proxy Error]', err.message);
        res.writeHead(500, {
          'Content-Type': 'application/json',
        });
        res.end(JSON.stringify({ 
          error: 'Proxy error', 
          message: err.message,
          hint: 'Make sure the backend is running on ' + target
        }));
      },
    })
  );
};
