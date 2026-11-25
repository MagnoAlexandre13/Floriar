"""Evolução aditiva do banco existente, preservando os pedidos já gravados."""

import sqlite3


class MigrationQueries:
    @staticmethod
    def add_order_owner(connection: sqlite3.Connection) -> None:
        columns = {row["name"] for row in connection.execute("PRAGMA table_info(orders)")}
        if "user_id" not in columns:
            connection.execute("ALTER TABLE orders ADD COLUMN user_id TEXT REFERENCES users(id)")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id, created_at DESC)")

    @staticmethod
    def add_bouquet_customization(connection: sqlite3.Connection) -> None:
        columns = {row["name"] for row in connection.execute("PRAGMA table_info(order_items)")}
        if "color" not in columns:
            connection.execute("""ALTER TABLE order_items ADD COLUMN color TEXT NOT NULL DEFAULT 'original'
                               CHECK (color IN ('original', 'yellow', 'pink', 'white', 'red', 'lilac'))""")
        if "description" not in columns:
            connection.execute("""ALTER TABLE order_items ADD COLUMN description TEXT NOT NULL DEFAULT ''
                               CHECK (length(description) <= 1000)""")
