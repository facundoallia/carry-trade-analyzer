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
    description="Professional carry trade analysis for Argentine bonds and treasury notes"
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
    """Clear in-memory cache endpoint for debugging"""
    global cache
    cache.clear()
    logger.info("In-memory cache cleared")
    return {"status": "in-memory cache cleared", "timestamp": datetime.now().isoformat()}

@app.get("/api/rem/cache/info")
async def get_rem_cache_info():
    """Get REM cache information"""
    try:
        cache_info = calculator.rem_fetcher.get_cache_info()
        return {
            "status": "success",
            "cache_info": cache_info,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting REM cache info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting cache info: {str(e)}")

@app.post("/api/rem/cache/clear")
async def clear_rem_cache():
    """Clear REM persistent cache (forces refresh on next request)"""
    try:
        calculator.rem_fetcher.clear_cache()
        logger.info("REM cache cleared (disk + memory)")
        return {
            "status": "success",
            "message": "REM cache cleared successfully",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error clearing REM cache: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error clearing cache: {str(e)}")

@app.post("/api/rem/cache/refresh")
async def refresh_rem_cache():
    """Force refresh of REM data from API"""
    try:
        logger.info("Forcing REM cache refresh")
        calculator.rem_fetcher.fetch_ipc_projections(force_refresh=True)
        cache_info = calculator.rem_fetcher.get_cache_info()
        return {
            "status": "success",
            "message": "REM data refreshed successfully",
            "cache_info": cache_info,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error refreshing REM cache: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error refreshing cache: {str(e)}")

@app.get("/api/rem-data")
@limiter.limit("30/minute")
async def get_rem_data(request: Request):
    """Get REM IPC data for methodology section display"""
    try:
        import requests as req
        from backend.config import KNOWN_INFLATION_DATA, REM_API_BASE_URL

        rem_data = calculator.rem_fetcher.fetch_ipc_projections()

        # Extract monthly and annual projections
        monthly_projections = []
        annual_projections = []
        seen_monthly = set()

        if rem_data and 'datos' in rem_data:
            logger.info(f"REM data has {len(rem_data['datos'])} rows")
            for row in rem_data.get('datos', []):
                periodo = row.get('período', row.get('periodo', ''))
                referencia = str(row.get('referencia', '')).lower()
                mediana = row.get('mediana', row.get('Mediana'))
                if mediana is None:
                    continue

                parsed_date = calculator.rem_fetcher._parse_period_to_date(periodo)

                # Monthly projections: has a parseable date with specific month
                # Use same approach as carry_calculator (no strict referencia filter)
                if parsed_date and parsed_date.year >= 2025:
                    month_key = parsed_date.strftime('%Y-%m')
                    # Check if it's a monthly data point (not annual)
                    if 'i.a.' not in referencia and 'dic' not in referencia and 'próx' not in referencia:
                        if month_key not in seen_monthly:
                            seen_monthly.add(month_key)
                            monthly_projections.append({
                                'periodo': month_key,
                                'mediana': round(float(mediana), 2),
                                'participantes': row.get('cantidad_de_participantes'),
                            })
                    # Annual projections
                    elif 'i.a.' in referencia or 'dic' in referencia:
                        annual_projections.append({
                            'periodo': str(parsed_date.year),
                            'referencia': row.get('referencia', ''),
                            'mediana': round(float(mediana), 2),
                        })
                # Annual projections without parseable month (e.g. "2026", "2027")
                elif not parsed_date and ('i.a.' in referencia or 'dic' in referencia):
                    label = str(periodo).strip()
                    annual_projections.append({
                        'periodo': label,
                        'referencia': row.get('referencia', ''),
                        'mediana': round(float(mediana), 2),
                    })
        else:
            logger.warning(f"REM data is empty or missing 'datos' key. rem_data type: {type(rem_data)}")

        # Sort monthly by period
        monthly_projections.sort(key=lambda x: x['periodo'])

        logger.info(f"REM endpoint: {len(monthly_projections)} monthly, {len(annual_projections)} annual projections")

        # Known inflation
        known = [{'periodo': d.strftime('%Y-%m'), 'tasa': round(r * 100, 1)}
                 for d, r in KNOWN_INFLATION_DATA.items()]

        # Fetch metadata (non-blocking, uses separate endpoint)
        metadata = None
        try:
            resp = req.get(f"{REM_API_BASE_URL}/api/metadata", timeout=5, verify=False)
            if resp.ok:
                metadata = resp.json()
        except Exception:
            pass

        return {
            'monthly_projections': monthly_projections,
            'annual_projections': annual_projections,
            'known_inflation': known,
            'metadata': metadata,
            'titulo': rem_data.get('titulo', 'IPC General') if rem_data else 'IPC General',
            'timestamp': datetime.now().isoformat(),
            'status': 'success',
        }
    except Exception as e:
        logger.error(f"Error getting REM data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting REM data: {str(e)}")

@app.get("/api/inflation-projections")
async def get_inflation_projections():
    """Get inflation projections for transparency"""
    try:
        from backend.config import KNOWN_INFLATION_DATA

        # Get REM data
        rem_data = calculator.rem_fetcher.fetch_ipc_projections()

        # Build monthly REM data
        monthly_rem = {}
        if rem_data and 'datos' in rem_data:
            for row in rem_data.get('datos', []):
                periodo = row.get('período', '')
                mediana = row.get('mediana', row.get('Mediana'))
                if mediana and periodo:
                    parsed_date = calculator.rem_fetcher._parse_period_to_date(periodo)
                    if parsed_date and parsed_date.year >= 2026:
                        monthly_rem[parsed_date.strftime('%Y-%m')] = {
                            'value': float(mediana),
                            'period': periodo
                        }

        # Get annual projections
        annual_projections = {}
        if rem_data and 'datos' in rem_data:
            for row in rem_data.get('datos', []):
                periodo = str(row.get('período', '')).strip()
                if periodo.isdigit() and int(periodo) >= 2026:
                    mediana = row.get('mediana')
                    if mediana:
                        annual_projections[periodo] = float(mediana)

        # Format known data
        known_data = {}
        for date_key, rate in KNOWN_INFLATION_DATA.items():
            known_data[date_key.strftime('%Y-%m')] = {
                'value': rate * 100,
                'source': 'INDEC'
            }

        return {
            "status": "success",
            "known_inflation": known_data,
            "monthly_rem_projections": monthly_rem,
            "annual_rem_projections": annual_projections,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting inflation projections: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting projections: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)