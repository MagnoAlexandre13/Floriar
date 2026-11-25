"""Configuração da aplicação. Execute: python -m uvicorn backend.main:app --reload."""

from contextlib import asynccontextmanager
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .database import BACKEND_DIR, Database
from .exception_handlers import register_exception_handlers
from .routes import router
from .schemas.errors import ErrorResponse

PROJECT_DIR = BACKEND_DIR.parent


def create_app(database_path: str | Path | None = None) -> FastAPI:
    database = Database(database_path or os.getenv("PETAL_DB_PATH") or BACKEND_DIR / "data" / "store.sqlite3")

    @asynccontextmanager
    async def lifespan(application):
        database.initialize()
        yield

    app = FastAPI(
        title="Petal & Stem — API da floricultura",
        version="1.0.0",
        description=("API acadêmica local para catálogo e pedidos demonstrativos. Valores dos pedidos em "
                     "centavos de USD. Contas e sessões autenticadas; sem pagamentos ou entregas reais."),
        lifespan=lifespan,
        responses={
            401: {"description": "Sessão ausente ou expirada.", "model": ErrorResponse},
            403: {"description": "Permissão ou token CSRF inválido.", "model": ErrorResponse},
            404: {"description": "Recurso não encontrado.", "model": ErrorResponse},
            409: {"description": "Transição de estado inválida.", "model": ErrorResponse},
            422: {"description": "Dados ou regras de entrega inválidos.", "model": ErrorResponse},
            503: {"description": "Banco temporariamente indisponível.", "model": ErrorResponse},
            429: {"description": "Limite de tentativas de login excedido.", "model": ErrorResponse},
        },
    )
    app.state.database = database
    app.state.cookie_secure = os.getenv("PETAL_COOKIE_SECURE", "false").lower() == "true"
    app.state.allowed_origins = ["http://127.0.0.1:4173", "http://localhost:4173"]

    @app.middleware("http")
    async def private_responses(request, call_next):
        response = await call_next(request)
        if request.url.path.startswith(("/api/auth", "/api/pedidos")):
            response.headers["Cache-Control"] = "no-store"
        return response
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app.state.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH"],
        allow_headers=["Content-Type", "X-CSRF-Token"],
    )
    register_exception_handlers(app)
    app.include_router(router)
    # Registrada por último para preservar /api, /docs, /openapi.json e /cliente.
    app.mount("/", StaticFiles(directory=PROJECT_DIR / "dist", html=True), name="storefront")
    return app


app = create_app()
