"""Schema do catálogo de buquês."""

from pydantic import BaseModel, Field
from .common import Color


class Product(BaseModel):
    id: str
    name: str
    price: float = Field(description="Preço base em dólares americanos (USD).")
    price_cents: int
    lead: int
    tag: str
    short: str
    description: str
    varieties: str
    palette: str
    color: str
    swatches: list[str]
    occasions: list[str]
    style: str
    alt: str
    colors: list[Color]
