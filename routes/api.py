from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["api"])

# Include route files
from routes.auth import router as auth_router
from routes.users import router as user_router

router.include_router(auth_router)
router.include_router(user_router)
