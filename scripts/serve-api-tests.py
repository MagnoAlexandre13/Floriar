"""Servidor isolado do Playwright, com administrador exclusivo de testes."""

import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import uvicorn

from backend.controllers.auth import AuthController
from backend.database import Database
from backend.schemas.auth import Register

database_path = Path(os.environ["PETAL_DB_PATH"]).resolve()
if not database_path.parent.name.startswith("petal-api-browser-"):
    raise SystemExit("Este servidor aceita apenas bancos temporários do Playwright.")
database = Database(database_path)
database.initialize()
AuthController(database).create_user(Register(name="Admin de testes", email="admin-browser@example.com",
                                             password="senha-browser-apenas-testes"), role="admin")
uvicorn.run("backend.main:app", host="127.0.0.1", port=8001)
