"""Conexões SQLite curtas, transações e carga inicial do catálogo."""

from contextlib import contextmanager
import json
from pathlib import Path
import sqlite3

from .queries.products import ProductQueries
from .queries.migrations import MigrationQueries

BACKEND_DIR = Path(__file__).resolve().parent


class Database:
    def __init__(self, path: str | Path):
        self.path = Path(path).resolve()

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    @contextmanager
    def transaction(self, *, write: bool = False):
        """Compartilha a mesma conexão em toda a operação e desfaz em caso de erro."""
        with self.connect() as connection:
            connection.execute("BEGIN IMMEDIATE" if write else "BEGIN")
            yield connection

    def initialize(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        products = json.loads((BACKEND_DIR / "catalog.json").read_text(encoding="utf-8"))
        with self.connect() as connection:
            connection.execute("PRAGMA journal_mode = WAL")
            connection.executescript((BACKEND_DIR / "schema.sql").read_text(encoding="utf-8"))
            connection.execute("BEGIN IMMEDIATE")
            MigrationQueries.add_bouquet_customization(connection)
            MigrationQueries.add_order_owner(connection)
            ProductQueries.seed_catalog(connection, products)
