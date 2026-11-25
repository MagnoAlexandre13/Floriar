"""Converte erros de negócio, validação e SQLite para respostas HTTP JSON."""

import sqlite3

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .exceptions import ShopError


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ShopError)
    async def shop_error(request: Request, error: ShopError):
        return JSONResponse(status_code=error.status_code,
                            content={"error": {"code": error.code, "message": error.message}})

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, error: RequestValidationError):
        # Não devolve mensagens de presente nem todo o corpo enviado nos erros.
        details = [{"location": list(item["loc"]), "message": item["msg"], "type": item["type"]}
                   for item in error.errors()]
        return JSONResponse(status_code=422, content=jsonable_encoder({"error": {
            "code": "validation_error", "message": "Confira os campos enviados.", "details": details}}))

    @app.exception_handler(sqlite3.OperationalError)
    async def database_error(request: Request, error: sqlite3.OperationalError):
        return JSONResponse(status_code=503, content={"error": {
            "code": "database_unavailable", "message": "Banco indisponível. Tente novamente."}})
