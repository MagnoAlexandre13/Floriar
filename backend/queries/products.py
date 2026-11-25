"""Consultas e carga inicial de produtos; recebe a conexão da transação ativa."""

from decimal import Decimal
import json
import sqlite3


def product_from_row(row: sqlite3.Row) -> dict:
    return {**json.loads(row["details"]), "id": row["id"], "name": row["name"],
            "price": row["price_cents"] / 100, "price_cents": row["price_cents"],
            "lead": row["lead_days"]}


class ProductQueries:
    @staticmethod
    def list_products(connection: sqlite3.Connection) -> list[dict]:
        return [product_from_row(row) for row in connection.execute("SELECT * FROM products ORDER BY rowid")]

    @staticmethod
    def get_product(connection: sqlite3.Connection, product_id: str) -> dict | None:
        row = connection.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
        return product_from_row(row) if row is not None else None

    @staticmethod
    def seed_catalog(connection: sqlite3.Connection, products: list[dict]) -> None:
        for product in products:
            details = {key: value for key, value in product.items() if key not in {"id", "name", "price", "lead"}}
            connection.execute(
                """INSERT INTO products (id, name, price_cents, lead_days, details)
                   VALUES (?, ?, ?, ?, ?) ON CONFLICT(id) DO UPDATE SET
                   name = excluded.name, details = excluded.details""",
                (product["id"], product["name"], int(Decimal(str(product["price"])) * 100),
                 product["lead"], json.dumps(details, ensure_ascii=False)),
            )
