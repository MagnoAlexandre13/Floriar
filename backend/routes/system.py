from fastapi import APIRouter, Response

from ..dependencies import SystemControllerDependency

router = APIRouter(prefix="/api", tags=["Sistema"])


@router.get("/health", summary="Verificar conexão com o banco")
def health(controller: SystemControllerDependency, response: Response) -> dict[str, str]:
    response.headers["X-Petal-Service"] = "petal-and-stem"
    response.headers["Cache-Control"] = "no-store"
    return controller.health()
