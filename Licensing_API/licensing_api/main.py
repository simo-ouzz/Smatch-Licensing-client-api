import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from licensing_api.api.licenses import router as licenses_router
from licensing_api.api.products import router as products_router
from licensing_api.api.auth import router as auth_router
from licensing_api.api.users import router as users_router
from licensing_api.api.api_keys import router as api_keys_router


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

static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", tags=["dashboard"])
async def dashboard():
    return FileResponse(os.path.join(static_dir, "dashboard", "index.html"))


@app.get("/dashboard", tags=["dashboard"])
async def dashboard_page():
    return FileResponse(os.path.join(static_dir, "dashboard", "index.html"))


@app.get("/health", tags=["health"])
async def health_check() -> dict:
    return {"status": "ok"}


app.include_router(auth_router, tags=["authentication"])
app.include_router(users_router, tags=["users"])
app.include_router(api_keys_router, tags=["api-keys"])
app.include_router(licenses_router, prefix="/licenses", tags=["licenses"])
app.include_router(products_router, prefix="/products", tags=["products"])
