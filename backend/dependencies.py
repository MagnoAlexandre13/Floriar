"""Injeta o banco da aplicação nos controllers de cada requisição."""

from typing import Annotated

from fastapi import Depends, Header, Request
from fastapi.security import APIKeyCookie
import hmac

from .controllers.delivery import DeliveryController
from .controllers.orders import OrderController
from .controllers.products import ProductController
from .controllers.system import SystemController
from .database import Database
from .controllers.auth import AuthController
from .exceptions import ShopError
from .security import SESSION_COOKIE


def get_database(request: Request) -> Database:
    return request.app.state.database


DatabaseDependency = Annotated[Database, Depends(get_database)]


def get_product_controller(database: DatabaseDependency) -> ProductController:
    return ProductController(database)


def get_order_controller(database: DatabaseDependency) -> OrderController:
    return OrderController(database)


def get_delivery_controller(
    products: Annotated[ProductController, Depends(get_product_controller)],
) -> DeliveryController:
    return DeliveryController(products)


def get_system_controller(database: DatabaseDependency) -> SystemController:
    return SystemController(database)


ProductControllerDependency = Annotated[ProductController, Depends(get_product_controller)]
OrderControllerDependency = Annotated[OrderController, Depends(get_order_controller)]
DeliveryControllerDependency = Annotated[DeliveryController, Depends(get_delivery_controller)]
SystemControllerDependency = Annotated[SystemController, Depends(get_system_controller)]


def get_auth_controller(database: DatabaseDependency) -> AuthController:
    return AuthController(database)


AuthControllerDependency = Annotated[AuthController, Depends(get_auth_controller)]
session_cookie = APIKeyCookie(name=SESSION_COOKIE, auto_error=False, scheme_name="SessionCookie")


def validate_origin(request: Request) -> None:
    origin = request.headers.get("origin")
    own_origin = str(request.base_url).rstrip("/")
    if ((origin and origin not in {*request.app.state.allowed_origins, own_origin})
            or request.headers.get("sec-fetch-site") == "cross-site"):
        raise ShopError(403, "untrusted_origin", "Origem da requisição não permitida.")


def get_session(controller: AuthControllerDependency,
                token: Annotated[str | None, Depends(session_cookie)]) -> dict:
    return controller.authenticate(token)


SessionDependency = Annotated[dict, Depends(get_session)]


def get_current_user(session: SessionDependency) -> dict:
    return session["user"]


def get_write_session(request: Request, session: SessionDependency,
                      csrf_token: Annotated[str | None, Header(alias="X-CSRF-Token")] = None) -> dict:
    validate_origin(request)
    if not csrf_token or not hmac.compare_digest(csrf_token.encode(), session["csrf_token"].encode()):
        raise ShopError(403, "invalid_csrf_token", "Atualize a página e tente novamente.")
    return session


WriteSessionDependency = Annotated[dict, Depends(get_write_session)]


def get_write_user(session: WriteSessionDependency) -> dict:
    return session["user"]


CurrentUserDependency = Annotated[dict, Depends(get_current_user)]
WriteUserDependency = Annotated[dict, Depends(get_write_user)]
