"""Cálculo de preços, validação de pedidos e transições de estado."""

from datetime import datetime, timezone
import sqlite3
from uuid import uuid4

from ..database import Database
from ..exceptions import ShopError
from ..queries.orders import OrderQueries
from ..queries.products import ProductQueries
from ..schemas.orders import OrderCreate, OrderStatus
from . import delivery

SIZE_EXTRAS = {"petite": 0, "classic": 2000, "abundant": 4000}
VASE_CENTS = 1800
TRANSITIONS = {
    "recebido": {"em_preparacao", "cancelado"},
    "em_preparacao": {"enviado", "cancelado"},
    "enviado": {"entregue"},
    "entregue": set(),
    "cancelado": set(),
}


class OrderController:
    def __init__(self, database: Database):
        self.database = database

    @staticmethod
    def _order(connection: sqlite3.Connection, order_id: str) -> dict:
        order = OrderQueries.get_order(connection, order_id)
        if order is None:
            raise ShopError(404, "order_not_found", "Pedido não encontrado.")
        return order

    @staticmethod
    def _authorize(order: dict, actor: dict) -> None:
        if actor["role"] != "admin" and order["user_id"] != actor["id"]:
            raise ShopError(404, "order_not_found", "Pedido não encontrado.")

    def order(self, order_id: str, actor: dict) -> dict:
        with self.database.connect() as connection:
            order = self._order(connection, order_id)
            self._authorize(order, actor)
            return order

    def orders(self, status: OrderStatus | None, limit: int, offset: int, actor: dict) -> dict:
        value = status.value if status is not None else None
        owner_id = None if actor["role"] == "admin" else actor["id"]
        with self.database.transaction() as connection:
            total = OrderQueries.count_orders(connection, value, owner_id)
            ids = OrderQueries.list_order_ids(connection, value, limit, offset, owner_id)
            items = [self._order(connection, order_id) for order_id in ids]
        return {"items": items, "total": total, "limit": limit, "offset": offset}

    def create_order(self, payload: OrderCreate, actor: dict) -> dict:
        today = delivery.store_today()
        timestamp = datetime.now(timezone.utc).isoformat()
        order_id = str(uuid4())
        with self.database.transaction(write=True) as connection:
            items = []
            subtotal = delivery_total = 0
            for item in payload.items:
                product = ProductQueries.get_product(connection, item.product)
                if product is None:
                    raise ShopError(404, "product_not_found", f"Produto não encontrado: {item.product}.")
                if item.color not in product["colors"]:
                    raise ShopError(422, "invalid_bouquet_color", "Esta cor não está disponível para o buquê escolhido.")
                reason = delivery.date_reason(item.date, product["lead"], today)
                if reason:
                    raise ShopError(422, "invalid_delivery_date", f"{product['name']}: {reason}")
                fee = delivery.delivery_fee(item.zip)
                unit = product["price_cents"] + SIZE_EXTRAS[item.size] + (VASE_CENTS if item.vase else 0)
                subtotal += unit * item.quantity
                delivery_total += fee * item.quantity
                items.append({
                    "product_id": item.product, "product_name": product["name"], "size": item.size,
                    "quantity": item.quantity, "vase": int(item.vase), "zip": item.zip,
                    "date": item.date, "message": item.message, "color": item.color,
                    "description": item.description, "unit_price_cents": unit,
                    "delivery_fee_cents": fee, "line_total_cents": (unit + fee) * item.quantity,
                })
            OrderQueries.insert_order(connection, {
                "id": order_id, "user_id": actor["id"], "status": "recebido", "currency": "USD",
                "subtotal_cents": subtotal, "delivery_cents": delivery_total,
                "total_cents": subtotal + delivery_total, "created_at": timestamp, "updated_at": timestamp,
            })
            OrderQueries.insert_items(connection, order_id, items)
            return self._order(connection, order_id)

    def update_status(self, order_id: str, target: OrderStatus, actor: dict) -> dict:
        # Serializa a leitura e a alteração para impedir transições concorrentes inválidas.
        with self.database.transaction(write=True) as connection:
            order = self._order(connection, order_id)
            self._authorize(order, actor)
            if actor["role"] != "admin" and target != OrderStatus.CANCELADO:
                raise ShopError(403, "admin_required", "Apenas administradores podem atualizar as etapas do pedido.")
            if target.value == order["status"]:
                return order
            if target.value not in TRANSITIONS[order["status"]]:
                raise ShopError(409, "invalid_status_transition",
                                f"Não é permitido mudar de {order['status']} para {target.value}.")
            OrderQueries.update_status(connection, order_id, target.value, datetime.now(timezone.utc).isoformat())
            return self._order(connection, order_id)
