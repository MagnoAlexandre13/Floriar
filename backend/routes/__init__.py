"""Registro dos grupos de rotas HTTP."""

from fastapi import APIRouter

from . import auth, delivery, orders, pages, products, system

router = APIRouter()
router.include_router(auth.router)
router.include_router(system.router)
router.include_router(products.router)
router.include_router(delivery.router)
router.include_router(orders.router)
router.include_router(pages.router)
