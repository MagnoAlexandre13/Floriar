"""Schemas de frete e disponibilidade de datas."""

from datetime import date as Date
from typing import Literal

from pydantic import BaseModel, Field


class DeliveryQuote(BaseModel):
    zip: str
    currency: Literal["USD"] = "USD"
    fee_cents: int = Field(description="Frete por buquê; multiplicado pela quantidade.")


class DeliveryDate(BaseModel):
    date: Date
    available: bool
    reason: str | None
