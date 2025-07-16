from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pathlib import Path
import json
import os
import logging
import time
from datetime import date, datetime
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from backend.carry_calculator import CarryTradeCalculator

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Argentine Bond Carry Trade Analyzer", 
    version="1.0.0",
    description="Professional carry trade analysis for Argentine bonds"
)

# Add trusted host middleware for security
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure with your actual domain in production
)

# Enhanced CORS middleware for iframe embedding
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://logos-serviciosfinancieros.com.ar",
        "http://logos-serviciosfinancieros.com.ar",
        "https://*.logos-serviciosfinancieros.com.ar",
        "http://localhost:3000",
        "http://localhost:8000",
        "https://*.railway.app",
        "https://*.render.com",
        "*"  # Allow all origins for iframe embedding
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "ALLOWALL"  # Allow iframe embedding
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# Simple in-memory cache for API responses
cache = {}
CACHE_DURATION = 30  # 30 seconds

# Mount static files
static_path = Path(__file__).parent.parent / "frontend" / "static"
app.mount("/static", StaticFiles(directory=static_path), name="static")

# Initialize calculator
calculator = CarryTradeCalculator()

def get_cached_data(key: str):
    """Get cached data if still valid"""
    if key in cache:
        data, timestamp = cache[key]
        if time.time() - timestamp < CACHE_DURATION:
            return data
    return None

def set_cached_data(key: str, data):
    """Set data in cache with timestamp"""
    cache[key] = (data, time.time())

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main HTML page"""
    html_path = Path(__file__).parent.parent / "frontend" / "templates" / "index.html"
    try:
        with open(html_path, 'r', encoding='utf-8') as file:
            return HTMLResponse(content=file.read())
    except FileNotFoundError:
        logger.error("Index HTML file not found")
        return HTMLResponse(content="<h1>Index page not found</h1>", status_code=404)

@app.get("/api/carry-data")
@limiter.limit("30/minute")
async def get_carry_data(request: Request):
    """Get carry trade table data with caching"""
    try:
        # Check cache first
        cached_data = get_cached_data("carry_data")
        if cached_data:
            logger.info("Returning cached carry data")
            return cached_data
        
        logger.info("Fetching fresh carry data")
        table_data = calculator.get_table_data()
        color_limits = calculator.get_color_limits()
        mep_rate = calculator.get_mep_rate()
        
        response_data = {
            "data": table_data,
            "color_limits": color_limits,
            "mep_rate": mep_rate,
            "timestamp": datetime.now().isoformat(),
            "cached": False
        }
        
        # Cache the response
        set_cached_data("carry_data", response_data)
        
        return response_data
    except Exception as e:
        logger.error(f"Error calculating carry data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error calculating carry data: {str(e)}")

@app.get("/api/chart-data")
@limiter.limit("30/minute")
async def get_chart_data(request: Request):
    """Get chart data for breakeven vs band ceiling with caching"""
    try:
        # Check cache first
        cached_data = get_cached_data("chart_data")
        if cached_data:
            logger.info("Returning cached chart data")
            return cached_data
        
        logger.info("Fetching fresh chart data")
        chart_data = calculator.get_chart_data()
        
        response_data = {
            "chart_data": chart_data,
            "timestamp": datetime.now().isoformat(),
            "cached": False
        }
        
        # Cache the response
        set_cached_data("chart_data", response_data)
        
        return response_data
    except Exception as e:
        logger.error(f"Error generating chart data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error generating chart data: {str(e)}")

@app.get("/api/health")
async def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Test basic functionality
        mep_rate = calculator.get_mep_rate()
        
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "mep_rate": mep_rate,
            "cache_size": len(cache),
            "version": "1.0.0"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

@app.get("/api/cache/clear")
async def clear_cache():
    """Clear cache endpoint for debugging"""
    global cache
    cache.clear()
    logger.info("Cache cleared")
    return {"status": "cache cleared", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)