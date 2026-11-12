from fastapi import APIRouter

from app.api.v1 import auth, conflicts, health, projects, screening, search

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(projects.router)
api_router.include_router(search.router)
api_router.include_router(screening.router)
api_router.include_router(conflicts.router)
