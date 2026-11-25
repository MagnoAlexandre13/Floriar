"""Schemas de criação, consulta e atualização de pedidos."""

from datetime import date as Date, datetime
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, Field, StrictBool, StrictInt

from .common import Color, InputModel, Size


class OrderItemCreate(InputModel):
    product: str = Field(min_length=1, max_length=80)
    size: Size = "classic"
    quantity: Annotated[StrictInt, Field(ge=1, le=9)] = 1
    vase: StrictBool = False
    zip: str = Field(pattern=r"^[0-9]{5}$")
    date: str = Field(pattern=r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
    message: str = Field(default="", max_length=240)
    color: Color = "original"
    description: str = Field(default="", min_length=10, max_length=1000,
                             description="Como a pessoa imagina o buquê. Omitido em pedidos antigos.")


class OrderCreate(InputModel):
    items: list[OrderItemCreate] = Field(min_length=1, max_length=30)


class OrderStatus(StrEnum):
    RECEBIDO = "recebido"
    EM_PREPARACAO = "em_preparacao"
    ENVIADO = "enviado"
    ENTREGUE = "entregue"
    CANCELADO = "cancelado"


class OrderStatusUpdate(InputModel):
    status: OrderStatus


class OrderItem(BaseModel):
    id: int
    product_id: str
    product_name: str
    size: Size
    quantity: int
    vase: bool
    zip: str
    date: Date
    message: str
    color: Color
    description: str
    unit_price_cents: int
    delivery_fee_cents: int
    line_total_cents: int


class Order(BaseModel):
    id: str
    user_id: str | None
    status: OrderStatus
    currency: Literal["USD"]
    subtotal_cents: int
    delivery_cents: int
    total_cents: int
    created_at: datetime
    updated_at: datetime
    items: list[OrderItem]


class OrderPage(BaseModel):
    items: list[Order]
    total: int
    limit: int
    offset: int
