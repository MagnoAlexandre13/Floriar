"""Contratos de cadastro e sessão; a senha mantém os espaços digitados."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Login(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str = Field(max_length=254, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    password: str = Field(min_length=1, max_length=128, repr=False, json_schema_extra={"format": "password"})

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, value):
        return value.strip().lower() if isinstance(value, str) else value


class Register(Login):
    name: str = Field(min_length=2, max_length=100)
    password: str = Field(min_length=10, max_length=128, repr=False, json_schema_extra={"format": "password"})

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value):
        return value.strip() if isinstance(value, str) else value


class User(BaseModel):
    id: str
    name: str
    email: str
    role: Literal["customer", "admin"]
    created_at: datetime


class AuthSession(BaseModel):
    user: User
    csrf_token: str
