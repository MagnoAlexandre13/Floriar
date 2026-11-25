"""Cria um administrador local sem incluir senhas na linha de comando."""

import argparse
from getpass import getpass
import os

from pydantic import ValidationError

from .controllers.auth import AuthController
from .database import BACKEND_DIR, Database
from .exceptions import ShopError
from .queries.auth import AuthQueries
from .schemas.auth import Register


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", help="E-mail da conta administrativa")
    parser.add_argument("--promote", action="store_true", help="Promover uma conta já cadastrada, preservando sua senha")
    args = parser.parse_args()
    email = (args.email or input("E-mail: ")).strip().lower()
    database = Database(os.getenv("PETAL_DB_PATH") or BACKEND_DIR / "data" / "store.sqlite3")
    database.initialize()
    if args.promote:
        with database.transaction(write=True) as connection:
            user = AuthQueries.user_by_email(connection, email)
            if not user:
                raise SystemExit("Conta não encontrada. Cadastre-a primeiro ou execute sem --promote.")
            AuthQueries.promote_user(connection, user["id"])
        print(f"Conta {email} promovida a administradora.")
        return
    name = input("Nome: ")
    password = getpass("Senha (10 a 128 caracteres): ")
    if password != getpass("Confirme a senha: "):
        raise SystemExit("As senhas não conferem.")
    try:
        user = AuthController(database).create_user(Register(name=name, email=email, password=password), role="admin")
    except ValidationError:
        raise SystemExit("Confira o nome, o e-mail e o tamanho da senha (10 a 128 caracteres).") from None
    except ShopError as error:
        raise SystemExit(error.message + " Use --promote para promover uma conta existente.") from None
    print(f"Administrador criado: {user['email']}")


if __name__ == "__main__":
    main()
