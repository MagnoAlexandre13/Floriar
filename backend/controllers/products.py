"""Consulta do catálogo e aplicação dos filtros de produtos."""

from decimal import Decimal

from ..database import Database
from ..exceptions import ShopError
from ..queries.products import ProductQueries


class ProductController:
    def __init__(self, database: Database):
        self.database = database

    def products(self, color: str | None = None, budget: Decimal | None = None) -> list[dict]:
        budget_cents = int(budget * 100) if budget is not None else None
        with self.database.connect() as connection:
            products = ProductQueries.list_products(connection)
        return [product for product in products if (color is None or product["color"] == color)
                and (budget_cents is None or product["price_cents"] <= budget_cents)]

    def product(self, product_id: str) -> dict:
        with self.database.connect() as connection:
            product = ProductQueries.get_product(connection, product_id)
        if product is None:
            raise ShopError(404, "product_not_found", "Produto não encontrado.")
        return product
