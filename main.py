from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

from fastapi import FastAPI
from config import APP_NAME, APP_VERSION
from routes import router as api_router

app = FastAPI(title=APP_NAME, version=APP_VERSION)

# Include API routes
app.include_router(api_router)


@app.get("/")
def read_root():
    return {
        "app": APP_NAME,
        "version": APP_VERSION,
        "status": "running"
    }
