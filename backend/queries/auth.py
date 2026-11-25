"""Persistência de contas, sessões revogáveis e tentativas de login."""

import sqlite3


class AuthQueries:
    @staticmethod
    def user_by_email(connection: sqlite3.Connection, email: str) -> dict | None:
        row = connection.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        return dict(row) if row else None

    @staticmethod
    def insert_user(connection: sqlite3.Connection, user: dict) -> None:
        connection.execute("""INSERT INTO users (id, name, email, password_hash, role, created_at)
                              VALUES (:id, :name, :email, :password_hash, :role, :created_at)""", user)

    @staticmethod
    def promote_user(connection: sqlite3.Connection, user_id: str) -> None:
        connection.execute("UPDATE users SET role = 'admin' WHERE id = ?", (user_id,))

    @staticmethod
    def insert_session(connection: sqlite3.Connection, session: dict) -> None:
        connection.execute("DELETE FROM sessions WHERE expires_at <= ?", (session["created_at"],))
        connection.execute("""INSERT INTO sessions (token_hash, user_id, csrf_token, expires_at, created_at)
                              VALUES (:token_hash, :user_id, :csrf_token, :expires_at, :created_at)""", session)

    @staticmethod
    def session(connection: sqlite3.Connection, digest: str, now: int) -> dict | None:
        row = connection.execute("""SELECT users.*, sessions.csrf_token, sessions.token_hash
                                    FROM sessions JOIN users ON users.id = sessions.user_id
                                    WHERE sessions.token_hash = ? AND sessions.expires_at > ?""", (digest, now)).fetchone()
        return dict(row) if row else None

    @staticmethod
    def revoke_session(connection: sqlite3.Connection, digest: str) -> None:
        connection.execute("DELETE FROM sessions WHERE token_hash = ?", (digest,))

    @staticmethod
    def attempts(connection: sqlite3.Connection, key: str) -> dict | None:
        row = connection.execute("SELECT * FROM auth_attempts WHERE key_hash = ?", (key,)).fetchone()
        return dict(row) if row else None

    @staticmethod
    def record_failure(connection: sqlite3.Connection, key: str, now: int) -> None:
        connection.execute("DELETE FROM auth_attempts WHERE window_start <= ?", (now - 900,))
        connection.execute("""INSERT INTO auth_attempts VALUES (?, 1, ?)
                              ON CONFLICT(key_hash) DO UPDATE SET failures = failures + 1""", (key, now))

    @staticmethod
    def clear_failures(connection: sqlite3.Connection, key: str) -> None:
        connection.execute("DELETE FROM auth_attempts WHERE key_hash = ?", (key,))
