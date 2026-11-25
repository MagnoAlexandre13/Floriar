"""Leitura e gravação de pedidos, sem validação de estados ou cálculo de preços."""

import sqlite3


class OrderQueries:
    @staticmethod
    def filters(status: str | None, owner_id: str | None) -> tuple[str, tuple]:
        conditions, parameters = [], []
        if status is not None:
            conditions.append("status = ?")
            parameters.append(status)
        if owner_id is not None:
            conditions.append("user_id = ?")
            parameters.append(owner_id)
        return (" WHERE " + " AND ".join(conditions) if conditions else ""), tuple(parameters)

    @staticmethod
    def get_order(connection: sqlite3.Connection, order_id: str) -> dict | None:
        row = connection.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
        if row is None:
            return None
        items = []
        for item in connection.execute("SELECT * FROM order_items WHERE order_id = ? ORDER BY id", (order_id,)):
            data = dict(item)
            del data["order_id"]
            data["vase"] = bool(data["vase"])
            items.append(data)
        return {**dict(row), "items": items}

    @staticmethod
    def list_order_ids(connection: sqlite3.Connection, status: str | None, limit: int, offset: int,
                       owner_id: str | None = None) -> list[str]:
        where, parameters = OrderQueries.filters(status, owner_id)
        rows = connection.execute("SELECT id FROM orders" + where +
                                  " ORDER BY created_at DESC, id LIMIT ? OFFSET ?",
                                  (*parameters, limit, offset)).fetchall()
        return [row["id"] for row in rows]

    @staticmethod
    def count_orders(connection: sqlite3.Connection, status: str | None, owner_id: str | None = None) -> int:
        where, parameters = OrderQueries.filters(status, owner_id)
        return connection.execute("SELECT count(*) FROM orders" + where, parameters).fetchone()[0]

    @staticmethod
    def insert_order(connection: sqlite3.Connection, order: dict) -> None:
        connection.execute(
            """INSERT INTO orders
               (id, user_id, status, currency, subtotal_cents, delivery_cents, total_cents, created_at, updated_at)
               VALUES (:id, :user_id, :status, :currency, :subtotal_cents, :delivery_cents, :total_cents,
                       :created_at, :updated_at)""", order,
        )

    @staticmethod
    def insert_items(connection: sqlite3.Connection, order_id: str, items: list[dict]) -> None:
        connection.executemany(
            """INSERT INTO order_items
               (order_id, product_id, product_name, size, quantity, vase, zip, date, message, color, description,
                unit_price_cents, delivery_fee_cents, line_total_cents)
               VALUES (:order_id, :product_id, :product_name, :size, :quantity, :vase, :zip, :date,
                       :message, :color, :description, :unit_price_cents, :delivery_fee_cents, :line_total_cents)""",
            [{"order_id": order_id, **item} for item in items],
        )

    @staticmethod
    def update_status(connection: sqlite3.Connection, order_id: str, status: str, updated_at: str) -> None:
        connection.execute("UPDATE orders SET status = ?, updated_at = ? WHERE id = ?",
                           (status, updated_at, order_id))
