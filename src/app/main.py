from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.ocr import router as ocr_router
from app.api.qr import router as qr_router
from app.api.split import router as split_router
from app.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, debug=settings.app_debug)
    app.include_router(health_router)
    app.include_router(ocr_router)
    app.include_router(qr_router)
    app.include_router(split_router)
    return app


app = create_app()
