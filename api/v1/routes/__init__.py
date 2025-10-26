from fastapi import APIRouter
from api.v1.routes.auth import auth
from api.v1.routes.project import router as project_router
from api.v1.routes.donation import router as donation_router
from api.v1.routes.trace import router as trace_router


api_version_one = APIRouter(prefix="/api/v1")
api_version_one.include_router(auth)
api_version_one.include_router(project_router)
api_version_one.include_router(donation_router)
api_version_one.include_router(trace_router)
