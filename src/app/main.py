from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.openapi.docs import (
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from fastapi.staticfiles import StaticFiles

from app.api.health import router as health_router
from app.api.ocr import router as ocr_router
from app.api.qr import router as qr_router
from app.api.split import router as split_router
from app.config import get_settings

_OPENAPI_DOCS_STATIC = Path(__file__).resolve().parent / "static"


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        debug=settings.app_debug,
        docs_url=None,
        redoc_url=None,
    )
    app.mount(
        "/openapi-docs-static",
        StaticFiles(directory=str(_OPENAPI_DOCS_STATIC)),
        name="openapi_docs_static",
    )

    @app.get("/docs", include_in_schema=False)
    async def swagger_ui_html() -> HTMLResponse:
        return get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=f"{app.title} - Swagger UI",
            oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
            swagger_js_url="/openapi-docs-static/swagger-ui/swagger-ui-bundle.js",
            swagger_css_url="/openapi-docs-static/swagger-ui/swagger-ui.css",
            swagger_favicon_url="",
        )

    @app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
    async def swagger_ui_redirect() -> HTMLResponse:
        return get_swagger_ui_oauth2_redirect_html()

    app.include_router(health_router)
    app.include_router(ocr_router)
    app.include_router(qr_router)
    app.include_router(split_router)
    return app


app = create_app()
