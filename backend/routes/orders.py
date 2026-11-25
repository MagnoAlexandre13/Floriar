"""Endpoints de criação, consulta, paginação e atualização de pedidos."""

from uuid import UUID

from fastapi import APIRouter, Query, Response

from ..dependencies import CurrentUserDependency, OrderControllerDependency, WriteUserDependency
from ..schemas.orders import Order, OrderCreate, OrderPage, OrderStatus, OrderStatusUpdate

router = APIRouter(prefix="/api/pedidos", tags=["Pedidos"])


@router.post("", response_model=Order, status_code=201, summary="Criar um pedido demonstrativo")
def create_order(payload: OrderCreate, response: Response, controller: OrderControllerDependency,
                 actor: WriteUserDependency):
    """Valida todos os itens e grava o pedido em uma única transação.

    Os preços e os totais vêm do banco. O corpo aceita apenas `items`,
    com os campos `product`, `size`, `quantity`, `vase`, `zip`, `date`, `message`,
    `color` e `description`. A cor deve constar em `colors` do produto.
    Repetir um POST cria outro pedido; não existe chave de idempotência.
    """
    order = controller.create_order(payload, actor)
    response.headers["Location"] = f"/api/pedidos/{order['id']}"
    return order


@router.get("", response_model=OrderPage, summary="Listar pedidos com paginação")
def orders(controller: OrderControllerDependency, actor: CurrentUserDependency, status: OrderStatus | None = None,
           limit: int = Query(default=20, ge=1, le=100), offset: int = Query(default=0, ge=0)):
    return controller.orders(status, limit, offset, actor)


@router.get("/{order_id}", response_model=Order, summary="Consultar pedido")
def order(order_id: UUID, controller: OrderControllerDependency, actor: CurrentUserDependency):
    return controller.order(str(order_id), actor)


@router.patch("/{order_id}/status", response_model=Order, summary="Alterar o estado de um pedido")
def update_status(order_id: UUID, payload: OrderStatusUpdate, controller: OrderControllerDependency,
                  actor: WriteUserDependency):
    """recebido → em_preparacao → enviado → entregue.

    Cancelamento permitido em recebido e em_preparacao. Repetir o estado atual
    retorna o pedido sem modificá-lo. Saltos e retorno de estados geram 409.
    """
    return controller.update_status(str(order_id), payload.status, actor)
