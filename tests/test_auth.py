from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from auth_helpers import PASSWORD, authenticate
from backend.main import create_app
from backend.security import SESSION_COOKIE, SESSION_SECONDS, hash_password, token_hash, verify_password


class AuthenticationTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name) / "auth.sqlite3"
        self.app = create_app(self.path)
        self.client = TestClient(self.app)
        self.client.__enter__()
        self.addCleanup(self.directory.cleanup)
        self.addCleanup(self.client.__exit__, None, None, None)

    def register(self, client=None, email="cliente@example.com", password=PASSWORD):
        return (client or self.client).post("/api/auth/cadastro", json={
            "name": "Pessoa de teste", "email": email, "password": password})

    def payload(self):
        dates = self.client.get("/api/produtos/sunday-morning/datas").json()
        date = next(item["date"] for item in dates if item["available"])
        return {"items": [{"product": "sunday-morning", "zip": "97201", "date": date}]}

    def test_registration_cookie_and_password_storage(self):
        response = self.register(email="  Cliente@Example.com  ")
        self.assertEqual(response.status_code, 201, response.text)
        user = response.json()["user"]
        self.assertEqual(user["email"], "cliente@example.com")
        self.assertEqual(user["role"], "customer")
        self.assertNotIn("password", response.text)
        self.assertNotIn("token_hash", response.text)
        cookie = response.headers["set-cookie"].lower()
        self.assertIn("httponly", cookie)
        self.assertIn("samesite=lax", cookie)
        self.assertIn("max-age=28800", cookie)
        self.assertEqual(response.headers["cache-control"], "no-store")
        with self.app.state.database.connect() as connection:
            row = connection.execute("SELECT password_hash FROM users").fetchone()
            self.assertNotEqual(row[0], PASSWORD)
            self.assertTrue(verify_password(PASSWORD, row[0]))
            digest = connection.execute("SELECT token_hash FROM sessions").fetchone()[0]
            self.assertNotEqual(digest, self.client.cookies.get(SESSION_COOKIE))
            self.assertEqual(digest, token_hash(self.client.cookies.get(SESSION_COOKIE)))

    def test_password_hashes_have_salt_and_preserve_spaces(self):
        password = "  uma senha com espaços  "
        first, second = hash_password(password), hash_password(password)
        self.assertNotEqual(first, second)
        self.assertTrue(verify_password(password, first))
        self.assertFalse(verify_password(password.strip(), first))
        self.assertFalse(verify_password(password, "hash inválido"))
        self.assertEqual(self.register(password=password).status_code, 201)
        login = self.client.post("/api/auth/login", json={"email": "cliente@example.com", "password": password})
        self.assertEqual(login.status_code, 200)

    def test_duplicate_and_invalid_registration(self):
        self.assertEqual(self.register().status_code, 201)
        self.assertEqual(self.register(email="CLIENTE@EXAMPLE.COM").status_code, 409)
        self.assertEqual(self.register(email="invalido").status_code, 422)
        self.assertEqual(self.register(email="outra@example.com", password="curta").status_code, 422)
        response = self.client.post("/api/auth/cadastro", json={"name": "Teste", "email": "admin@example.com",
                                  "password": PASSWORD, "role": "admin"})
        self.assertEqual(response.status_code, 422)
        self.assertNotIn(PASSWORD, response.text)

    def test_login_errors_are_generic_and_session_rotates(self):
        self.register()
        original = self.client.cookies.get(SESSION_COOKIE)
        for email in ("cliente@example.com", "ausente@example.com"):
            response = self.client.post("/api/auth/login", json={"email": email, "password": "incorreta"})
            self.assertEqual(response.status_code, 401)
            self.assertEqual(response.json()["error"]["message"], "E-mail ou senha incorretos.")
        self.assertEqual(self.client.post("/api/auth/login", json={"email": "cliente@example.com", "password": PASSWORD}).status_code, 200)
        self.assertNotEqual(self.client.cookies.get(SESSION_COOKIE), original)
        self.client.cookies.clear()
        self.client.cookies.set(SESSION_COOKIE, original)
        self.assertEqual(self.client.get("/api/auth/me").status_code, 401)

    def test_failed_login_limit_expires(self):
        self.register()
        now = int(time.time())
        for _ in range(5):
            self.assertEqual(self.client.post("/api/auth/login", json={"email": "cliente@example.com", "password": "errada"}).status_code, 401)
        self.assertEqual(self.client.post("/api/auth/login", json={"email": "cliente@example.com", "password": PASSWORD}).status_code, 429)
        with patch("backend.controllers.auth.time.time", return_value=now + 901):
            self.assertEqual(self.client.post("/api/auth/login", json={"email": "cliente@example.com", "password": PASSWORD}).status_code, 200)

    def test_orders_require_authentication_and_catalog_remains_public(self):
        self.assertEqual(self.client.get("/api/produtos").status_code, 200)
        self.assertEqual(self.client.get("/api/pedidos").status_code, 401)
        self.assertEqual(self.client.post("/api/pedidos", json=self.payload()).status_code, 401)
        self.assertEqual(self.client.get("/api/auth/me").status_code, 401)

    def test_csrf_is_required_for_writes_and_origin_is_checked(self):
        session = self.register().json()
        self.assertEqual(self.client.post("/api/pedidos", json=self.payload()).status_code, 403)
        self.client.headers["X-CSRF-Token"] = "invalido"
        self.assertEqual(self.client.post("/api/pedidos", json=self.payload()).status_code, 403)
        self.client.headers["X-CSRF-Token"] = session["csrf_token"]
        response = self.client.post("/api/pedidos", json=self.payload(), headers={"Origin": "https://evil.example"})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.client.post("/api/pedidos", json=self.payload()).status_code, 201)
        for endpoint in ("login", "cadastro"):
            self.assertEqual(self.client.post(f"/api/auth/{endpoint}", json={}, headers={"Origin": "https://evil.example"}).status_code, 403)

    def test_logout_revokes_stolen_cookie_and_expiration_is_enforced(self):
        session = self.register().json()
        token = self.client.cookies.get(SESSION_COOKIE)
        self.assertEqual(self.client.post("/api/auth/logout").status_code, 403)
        self.client.headers["X-CSRF-Token"] = session["csrf_token"]
        self.assertEqual(self.client.post("/api/auth/logout").status_code, 204)
        self.client.cookies.set(SESSION_COOKIE, token)
        self.assertEqual(self.client.get("/api/auth/me").status_code, 401)
        login = self.client.post("/api/auth/login", json={"email": "cliente@example.com", "password": PASSWORD})
        self.assertEqual(login.status_code, 200)
        with patch("backend.controllers.auth.time.time", return_value=int(time.time()) + SESSION_SECONDS + 1):
            self.assertEqual(self.client.get("/api/auth/me").status_code, 401)

    def test_customer_cannot_access_other_customers_orders_or_progress_status(self):
        alice = authenticate(self.client, admin=False, email="alice@example.com")["user"]
        alice_order = self.client.post("/api/pedidos", json=self.payload()).json()
        self.assertEqual(alice_order["user_id"], alice["id"])
        with TestClient(self.app) as bob:
            authenticate(bob, admin=False, email="bob@example.com")
            self.assertEqual(bob.get("/api/pedidos").json()["total"], 0)
            path = f"/api/pedidos/{alice_order['id']}"
            self.assertEqual(bob.get(path).status_code, 404)
            self.assertEqual(bob.patch(path + "/status", json={"status": "cancelado"}).status_code, 404)
        path = f"/api/pedidos/{alice_order['id']}/status"
        self.assertEqual(self.client.patch(path, json={"status": "enviado"}).status_code, 403)
        self.assertEqual(self.client.patch(path, json={"status": "cancelado"}).status_code, 200)

    def test_admin_access_and_legacy_order_migration(self):
        authenticate(self.client, admin=False)
        order = self.client.post("/api/pedidos", json=self.payload()).json()
        with self.app.state.database.connect() as connection:
            connection.execute("DROP INDEX idx_orders_user")
            connection.execute("ALTER TABLE orders DROP COLUMN user_id")
        with TestClient(create_app(self.path)) as upgraded:
            authenticate(upgraded, admin=False)
            self.assertEqual(upgraded.get(f"/api/pedidos/{order['id']}").status_code, 404)
            self.assertEqual(upgraded.get("/api/pedidos").json()["total"], 0)
            with upgraded.app.state.database.connect() as connection:
                connection.execute("UPDATE users SET role = 'admin' WHERE email = 'teste@example.com'")
            self.assertIsNone(upgraded.get(f"/api/pedidos/{order['id']}").json()["user_id"])
            self.assertEqual(upgraded.get("/api/pedidos").json()["total"], 1)
            self.assertEqual(upgraded.patch(f"/api/pedidos/{order['id']}/status", json={"status": "em_preparacao"}).status_code, 200)


if __name__ == "__main__":
    unittest.main()
