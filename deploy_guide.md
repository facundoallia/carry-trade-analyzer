# Deployment Guide - Argentine Carry Trade Analyzer

## Platform Deployment Instructions

### Railway Deployment

1. **Connect Repository**
   - Link your GitHub repository to Railway
   - Railway will automatically detect the Python application

2. **Environment Variables**
   - Set `PORT` (Railway will provide this automatically)
   - Set `ENVIRONMENT=production`
   - Set `LOG_LEVEL=INFO`

3. **Deploy Command**
   ```bash
   # Railway will automatically use the Procfile
   # No additional configuration needed
   ```

### Render Deployment

1. **Create Web Service**
   - Connect your GitHub repository
   - Choose "Web Service" type
   - Set build command: `pip install -r requirements.txt`
   - Set start command: `gunicorn -w 4 -k uvicorn.workers.UvicornWorker backend.main:app --host 0.0.0.0 --port $PORT`

2. **Environment Variables**
   - `ENVIRONMENT=production`
   - `LOG_LEVEL=INFO`
   - `PYTHON_VERSION=3.11.7`

## Features Enabled for Production

### Security & CORS
- ✅ CORS configured for iframe embedding
- ✅ Security headers (XSS protection, content type options)
- ✅ X-Frame-Options set to ALLOWALL for iframe support
- ✅ Rate limiting (30 requests/minute per IP)
- ✅ Trusted host middleware

### Performance Optimizations
- ✅ In-memory caching (30-second duration)
- ✅ Gunicorn with 4 workers
- ✅ Uvicorn ASGI server for async performance
- ✅ Static file serving optimization

### Monitoring & Logging
- ✅ Health check endpoint: `/api/health`
- ✅ Cache monitoring endpoint: `/api/cache/clear`
- ✅ Production logging with timestamps
- ✅ Error tracking and reporting

### API Endpoints
- `GET /` - Main web interface
- `GET /api/carry-data` - Carry trade analysis data (cached)
- `GET /api/chart-data` - Chart visualization data (cached)
- `GET /api/health` - Health check and monitoring
- `GET /api/cache/clear` - Cache management

### Error Handling
- ✅ Graceful API timeout handling
- ✅ Fallback MEP rate (1200.0)
- ✅ Comprehensive error logging
- ✅ HTTP 503 for service unavailability

## Iframe Embedding

The application is configured to be embedded in iframes from:
- `https://logos-serviciosfinancieros.com.ar`
- `https://*.logos-serviciosfinancieros.com.ar`
- All Railway and Render subdomains

### Sample Iframe Code
```html
<iframe 
  src="https://your-app-name.railway.app" 
  width="100%" 
  height="800px" 
  frameborder="0">
</iframe>
```

## Post-Deployment Verification

1. **Health Check**
   ```bash
   curl https://your-app-name.railway.app/api/health
   ```

2. **API Response Test**
   ```bash
   curl https://your-app-name.railway.app/api/carry-data
   ```

3. **Cache Performance**
   ```bash
   # First call (fresh data)
   curl https://your-app-name.railway.app/api/carry-data
   
   # Second call (cached data)
   curl https://your-app-name.railway.app/api/carry-data
   ```

## Troubleshooting

### Common Issues

1. **Port Configuration**
   - Railway/Render automatically set PORT environment variable
   - Application reads from `os.getenv("PORT", 8000)`

2. **CORS Issues**
   - Verify allowed origins in main.py
   - Check X-Frame-Options header

3. **API Timeouts**
   - data912.com API calls have 10-second timeout
   - Fallback MEP rate activates on failure

4. **Cache Issues**
   - Use `/api/cache/clear` to reset cache
   - Cache duration is 30 seconds by default

### Performance Monitoring

Monitor these metrics:
- Response times for `/api/carry-data`
- Cache hit/miss ratios
- Error rates from data912.com API
- Memory usage with caching

## Production Checklist

- [ ] Repository connected to hosting platform
- [ ] Environment variables configured
- [ ] Health check endpoint responding
- [ ] CORS headers allowing iframe embedding
- [ ] Rate limiting active
- [ ] Caching functional
- [ ] Error logging enabled
- [ ] API endpoints returning valid data
- [ ] Static files serving correctly
- [ ] Iframe embedding tested