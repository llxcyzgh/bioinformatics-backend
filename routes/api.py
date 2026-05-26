from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["api"])

# Include route files
from routes.auth import router as auth_router
from routes.project import router as project_router
from routes.user import router as user_router

router.include_router(auth_router)
router.include_router(project_router)
router.include_router(user_router)
