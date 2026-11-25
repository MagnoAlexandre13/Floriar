"""Endpoints do catálogo; as regras são delegadas ao ProductController."""

from decimal import Decimal

from fastapi import APIRouter, Query

from ..dependencies import ProductControllerDependency
from ..schemas.products import Product

router = APIRouter(prefix="/api/produtos", tags=["Produtos"])


@router.get("", response_model=list[Product], summary="Listar catálogo")
def products(controller: ProductControllerDependency,
             color: str | None = Query(default=None, max_length=40),
             budget: Decimal | None = Query(default=None, ge=0, le=100000)):
    """Filtros opcionais: `color=cream` e `budget=50` (preço base máximo em USD)."""
    return controller.products(color, budget)


@router.get("/{product_id}", response_model=Product, summary="Consultar produto")
def product(product_id: str, controller: ProductControllerDependency):
    return controller.product(product_id)
