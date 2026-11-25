"""Cadastro, validação de credenciais e ciclo de vida das sessões."""

from datetime import datetime, timezone
import secrets
import sqlite3
import time
from uuid import uuid4

from ..database import Database
from ..exceptions import ShopError
from ..queries.auth import AuthQueries
from ..schemas.auth import Login, Register
from ..security import DUMMY_PASSWORD_HASH, SESSION_SECONDS, hash_password, token_hash, verify_password


def public_user(user: dict) -> dict:
    return {key: user[key] for key in ("id", "name", "email", "role", "created_at")}


class AuthController:
    def __init__(self, database: Database):
        self.database = database

    def create_user(self, payload: Register, *, role: str = "customer") -> dict:
        user = {"id": str(uuid4()), "name": payload.name, "email": payload.email,
                "password_hash": hash_password(payload.password), "role": role,
                "created_at": datetime.now(timezone.utc).isoformat()}
        try:
            with self.database.transaction(write=True) as connection:
                AuthQueries.insert_user(connection, user)
        except sqlite3.IntegrityError:
            raise ShopError(409, "email_registered", "Este e-mail já está cadastrado.") from None
        return public_user(user)

    def start_session(self, user: dict, previous_token: str | None = None) -> tuple[dict, str]:
        token = secrets.token_urlsafe(32)
        csrf = secrets.token_urlsafe(32)
        now = int(time.time())
        with self.database.transaction(write=True) as connection:
            if previous_token:
                AuthQueries.revoke_session(connection, token_hash(previous_token))
            AuthQueries.insert_session(connection, {"token_hash": token_hash(token), "user_id": user["id"],
                                       "csrf_token": csrf, "expires_at": now + SESSION_SECONDS, "created_at": now})
        return {"user": public_user(user), "csrf_token": csrf}, token

    def login(self, payload: Login, previous_token: str | None = None) -> tuple[dict, str]:
        now = int(time.time())
        key = token_hash(payload.email)
        with self.database.connect() as connection:
            attempts = AuthQueries.attempts(connection, key)
            user = AuthQueries.user_by_email(connection, payload.email)
        if attempts and attempts["window_start"] > now - 900 and attempts["failures"] >= 5:
            raise ShopError(429, "too_many_attempts", "Muitas tentativas. Aguarde 15 minutos para tentar novamente.")
        encoded = user["password_hash"] if user else DUMMY_PASSWORD_HASH
        if not verify_password(payload.password, encoded) or user is None:
            with self.database.transaction(write=True) as connection:
                AuthQueries.record_failure(connection, key, now)
            raise ShopError(401, "invalid_credentials", "E-mail ou senha incorretos.")
        with self.database.connect() as connection:
            AuthQueries.clear_failures(connection, key)
        return self.start_session(user, previous_token)

    def authenticate(self, token: str | None) -> dict:
        if token and len(token) <= 128:
            with self.database.connect() as connection:
                session = AuthQueries.session(connection, token_hash(token), int(time.time()))
            if session:
                return {"user": public_user(session), "csrf_token": session["csrf_token"],
                        "token_hash": session["token_hash"]}
        raise ShopError(401, "authentication_required", "Entre na sua conta para continuar.")

    def logout(self, session: dict) -> None:
        with self.database.connect() as connection:
            AuthQueries.revoke_session(connection, session["token_hash"])
