"""
Main Application Entrypoint (FastAPI)
Configures middleware, mounts static files, registers API endpoints,
and serves the single-page frontend.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from contextlib import asynccontextmanager
import os

from app.database import init_db
from app.etl_seed import run_etl, seed_sample_analytics_history
from app.api import router as api_router

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
INDEX_FILE = STATIC_DIR / "index.html"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure schema and questions exist
    init_db()
    from app.database import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM questions;")
    count = cursor.fetchone()[0]
    conn.close()
    
    if count == 0:
        run_etl()
        seed_sample_analytics_history()
    yield
    # Shutdown logic if needed

# Initialize FastAPI instance
app = FastAPI(
    title="考 HSK Practice — Online Testing & Analytics Platform",
    description="Online Testing Platform for HSK Chinese Examination with Real-Time Analytics Pipeline",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for local testing and cross-origin calls
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Router
app.include_router(api_router)

# Mount static folder
if not STATIC_DIR.exists():
    STATIC_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "app": "HSK Online Testing Platform"}

# Serve Frontend SPA
@app.get("/", response_class=FileResponse, tags=["Frontend"])
def serve_home():
    if INDEX_FILE.exists():
        return FileResponse(str(INDEX_FILE))
    return {"message": "Frontend static/index.html not found"}

# Catch-all route to support client-side view routing
@app.get("/{full_path:path}", response_class=FileResponse, include_in_schema=False)
def catch_all(full_path: str):
    # If path starts with api/ or health, let FastAPI router handle
    if full_path.startswith("api/") or full_path == "health":
        return None
    file_path = STATIC_DIR / full_path
    if file_path.exists() and file_path.is_file():
        return FileResponse(str(file_path))
    if INDEX_FILE.exists():
        return FileResponse(str(INDEX_FILE))
    return {"message": "File not found"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
