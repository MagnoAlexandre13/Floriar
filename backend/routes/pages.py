"""Arquivos estáticos do cliente demonstrativo, fora do contrato REST."""

from fastapi import APIRouter
from fastapi.responses import FileResponse

from ..database import BACKEND_DIR

router = APIRouter()


@router.get("/cliente", response_class=FileResponse, include_in_schema=False)
def demo_client():
    return FileResponse(BACKEND_DIR / "client.html")


@router.get("/cliente.js", response_class=FileResponse, include_in_schema=False)
def demo_script():
    return FileResponse(BACKEND_DIR / "client.js", media_type="text/javascript")
