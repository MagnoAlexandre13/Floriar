"""Regras do calendário de Portland e cálculo de frete por buquê."""

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from ..exceptions import ShopError
from .products import ProductController

STORE_ZONE = ZoneInfo("America/Los_Angeles")


def store_today() -> date:
    return datetime.now(STORE_ZONE).date()


def delivery_fee(zip_code: str) -> int:
    if zip_code not in {"97201", "97202", "97203", "97204", "97205", "97206"}:
        raise ShopError(422, "delivery_unavailable", "Entrega disponível apenas nos ZIPs 97201 a 97206.")
    return 600 if zip_code in {"97201", "97202"} else 900


def date_reason(value: str, lead: int, today: date) -> str | None:
    try:
        requested = date.fromisoformat(value)
        if requested.isoformat() != value:
            raise ValueError
    except (ValueError, TypeError):
        return "Informe uma data válida no formato YYYY-MM-DD."
    if requested < today + timedelta(days=lead):
        return f"Este buquê precisa de {lead} dias de preparação."
    if requested > today + timedelta(days=30):
        return "Escolha uma data dentro dos próximos 30 dias."
    if requested.weekday() in {6, 0}:
        return "O estúdio fecha aos domingos e às segundas-feiras."
    if requested == today + timedelta(days=10):
        return "Esta data está lotada na simulação."
    return None


class DeliveryController:
    def __init__(self, products: ProductController):
        self.products = products

    def dates(self, product_id: str) -> list[dict]:
        product = self.products.product(product_id)
        today = store_today()
        dates = []
        for offset in range(2, 31):
            value = (today + timedelta(days=offset)).isoformat()
            reason = date_reason(value, product["lead"], today)
            dates.append({"date": value, "available": reason is None, "reason": reason})
        return dates

    def quote(self, zip_code: str) -> dict:
        return {"zip": zip_code, "currency": "USD", "fee_cents": delivery_fee(zip_code)}
