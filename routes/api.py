from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["api"])

# Include route files
from routes.auth import router as auth_router
from routes.project import router as project_router
from routes.task import router as task_router
from routes.user import router as user_router
from routes.template import router as template_router
from routes.chat import router as chat_router
from routes.upload import router as upload_router

router.include_router(auth_router)
router.include_router(project_router)
router.include_router(task_router)
router.include_router(user_router)
router.include_router(template_router)
router.include_router(chat_router)
router.include_router(upload_router)
