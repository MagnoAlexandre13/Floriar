"""Consulta de disponibilidade do banco."""

import sqlite3


class SystemQueries:
    @staticmethod
    def check_health(connection: sqlite3.Connection) -> None:
        connection.execute("SELECT 1 FROM products LIMIT 1").fetchone()
