import os
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import time

from licensing_api.api.licenses import router as licenses_router
from licensing_api.api.products import router as products_router
from licensing_api.api.auth import router as auth_router
from licensing_api.api.users import router as users_router
from licensing_api.api.api_keys import router as api_keys_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Licensing API",
    version="1.0.0",
    description="Production-ready licensing API backed by PostgreSQL and cryptographyyy core logic.",
)

allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {duration:.3f}s")
    return response

static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", tags=["dashboard"])
async def dashboard():
    return FileResponse(os.path.join(static_dir, "dashboard", "index.html"))


@app.get("/dashboard", tags=["dashboard"])
async def dashboard_page():
    return FileResponse(os.path.join(static_dir, "dashboard", "index.html"))


@app.get("/dashboard/", tags=["dashboard"])
async def dashboard_page_slash():
    return FileResponse(os.path.join(static_dir, "dashboard", "index.html"))


@app.get("/sdk-docs", tags=["documentation"])
async def docs_page():
    return FileResponse(os.path.join(static_dir, "docs.html"))


@app.get("/health", tags=["health"])
async def health_check() -> dict:
    return {"status": "ok"}


@app.on_event("startup")
async def startup_event():
    logger.info("=" * 50)
    logger.info("Starting Licensing API Server...")
    logger.info("=" * 50)


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("=" * 50)
    logger.info("Shutting down Licensing API Server...")
    logger.info("=" * 50)


app.include_router(auth_router, tags=["authentication"])
app.include_router(users_router, tags=["users"])
app.include_router(api_keys_router, tags=["api-keys"])
app.include_router(licenses_router, prefix="/licenses", tags=["licenses"])
app.include_router(products_router, prefix="/products", tags=["products"])
