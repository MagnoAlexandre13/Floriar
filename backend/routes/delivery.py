"""Endpoints de datas disponíveis e frete."""

from fastapi import APIRouter

from ..dependencies import DeliveryControllerDependency
from ..schemas.delivery import DeliveryDate, DeliveryQuote

router = APIRouter(prefix="/api", tags=["Entrega"])


@router.get("/produtos/{product_id}/datas", response_model=list[DeliveryDate],
            summary="Consultar datas de entrega de um produto")
def dates(product_id: str, controller: DeliveryControllerDependency):
    return controller.dates(product_id)


@router.get("/entrega/{zip_code}", response_model=DeliveryQuote, summary="Consultar frete por buquê")
def delivery(zip_code: str, controller: DeliveryControllerDependency):
    return controller.quote(zip_code)
