"""Cadastro, login, sessão atual e logout com cookie HttpOnly."""

from fastapi import APIRouter, Depends, Request, Response

from ..dependencies import (AuthControllerDependency, SessionDependency, WriteSessionDependency,
                            validate_origin)
from ..schemas.auth import AuthSession, Login, Register
from ..security import SESSION_COOKIE, SESSION_SECONDS

router = APIRouter(prefix="/api/auth", tags=["Autenticação"])


def set_session_cookie(request: Request, response: Response, token: str) -> None:
    response.set_cookie(SESSION_COOKIE, token, max_age=SESSION_SECONDS, path="/", httponly=True,
                        secure=request.app.state.cookie_secure, samesite="lax")
    response.headers["Cache-Control"] = "no-store"


@router.post("/cadastro", response_model=AuthSession, status_code=201,
             dependencies=[Depends(validate_origin)], summary="Criar conta de cliente e entrar")
def register(payload: Register, request: Request, response: Response, controller: AuthControllerDependency):
    user = controller.create_user(payload)
    session, token = controller.start_session(user, request.cookies.get(SESSION_COOKIE))
    set_session_cookie(request, response, token)
    return session


@router.post("/login", response_model=AuthSession, dependencies=[Depends(validate_origin)],
             summary="Entrar com e-mail e senha")
def login(payload: Login, request: Request, response: Response, controller: AuthControllerDependency):
    session, token = controller.login(payload, request.cookies.get(SESSION_COOKIE))
    set_session_cookie(request, response, token)
    return session


@router.get("/me", response_model=AuthSession, summary="Consultar usuário e token CSRF da sessão")
def me(response: Response, session: SessionDependency):
    response.headers["Cache-Control"] = "no-store"
    return {"user": session["user"], "csrf_token": session["csrf_token"]}


@router.post("/logout", status_code=204, summary="Revogar a sessão atual")
def logout(request: Request, response: Response, session: WriteSessionDependency,
           controller: AuthControllerDependency):
    controller.logout(session)
    response.delete_cookie(SESSION_COOKIE, path="/", httponly=True,
                           secure=request.app.state.cookie_secure, samesite="lax")
    response.headers["Cache-Control"] = "no-store"
