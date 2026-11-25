"""Senhas PBKDF2 com salt aleatório e tokens opacos de sessão."""

import hashlib
import hmac
import secrets

PASSWORD_ITERATIONS = 600_000
SESSION_SECONDS = 8 * 60 * 60
SESSION_COOKIE = "petal_session"


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), PASSWORD_ITERATIONS)
    return f"pbkdf2_sha256${PASSWORD_ITERATIONS}${salt}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt, expected = encoded.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), int(iterations))
        return hmac.compare_digest(actual.hex(), expected)
    except (ValueError, TypeError):
        return False


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


# Usuários inexistentes também fazem uma verificação completa de senha.
DUMMY_PASSWORD_HASH = hash_password(secrets.token_urlsafe(32))
