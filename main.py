from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from config import APP_NAME, APP_VERSION
from config.upload import UPLOAD_DIR
from routes import router as api_router

app = FastAPI(title=APP_NAME, version=APP_VERSION)

# Include API routes (must be before static mount)
app.include_router(api_router)

# Serve uploaded files at /uploads
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


@app.get("/")
def read_root():
    return {
        "app": APP_NAME,
        "version": APP_VERSION,
        "status": "running"
    }
