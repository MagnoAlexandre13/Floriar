"""Contas locais de teste, criadas apenas nos bancos temporários."""

from contextlib import contextmanager

from fastapi.testclient import TestClient

PASSWORD = "senha-de-teste-com-mais-de-10"


def authenticate(client, *, admin=True, email="teste@example.com"):
    payload = {"name": "Pessoa de teste", "email": email, "password": PASSWORD}
    response = client.post("/api/auth/cadastro", json=payload)
    if response.status_code == 409:
        response = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    assert response.status_code in (200, 201), response.text
    session = response.json()
    client.headers["X-CSRF-Token"] = session["csrf_token"]
    if admin:
        with client.app.state.database.connect() as connection:
            connection.execute("UPDATE users SET role = 'admin' WHERE id = ?", (session["user"]["id"],))
    return session


@contextmanager
def signed_client(app):
    with TestClient(app) as client:
        authenticate(client)
        yield client
