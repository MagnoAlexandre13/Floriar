"""Testes da API com banco temporário; não modificam os dados locais da loja."""

from datetime import date
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient
from auth_helpers import authenticate, signed_client

from backend.main import create_app
from backend.controllers.delivery import date_reason


class BackendTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.database_path = Path(self.directory.name) / "test.sqlite3"
        self.clock = patch("backend.controllers.delivery.store_today", return_value=date(2026, 11, 5))
        self.clock.start()
        self.app = create_app(self.database_path)
        self.client = TestClient(self.app)
        self.client.__enter__()
        authenticate(self.client)
        self.addCleanup(self.directory.cleanup)
        self.addCleanup(self.clock.stop)
        self.addCleanup(self.client.__exit__, None, None, None)
        self.item = {"product": "sunday-morning", "size": "classic", "quantity": 2,
                     "vase": True, "zip": "97201", "date": "2026-11-07", "message": "Para você <3"}

    def create_order(self):
        response = self.client.post("/api/pedidos", json={"items": [self.item]})
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def test_health_seed_catalog_and_filters(self):
        self.assertEqual(self.client.get("/api/health").json(), {"status": "ok"})
        products = self.client.get("/api/produtos").json()
        self.assertEqual(len(products), 5)
        self.assertEqual(products[0]["price_cents"], 4800)
        self.assertEqual(self.client.get("/api/produtos?color=cream&budget=50").json(), [products[0]])
        self.assertEqual(self.client.get("/api/produtos?color=rich&budget=50").json(), [])
        response = self.client.get("/api/produtos?budget=-1")
        self.assertEqual(response.status_code, 422)
        self.assertEqual(self.client.get("/api/produtos?budget=NaN").status_code, 422)

    def test_catalog_matches_existing_storefront(self):
        seed = json.loads((Path(__file__).resolve().parents[1] / "backend/catalog.json").read_text(encoding="utf-8"))
        for original, product in zip(seed, self.client.get("/api/produtos").json(), strict=True):
            for key, value in original.items():
                self.assertEqual(product[key], value)

    def test_product_lookup_and_unknown_product(self):
        self.assertEqual(self.client.get("/api/produtos/wild-at-heart").json()["lead"], 5)
        response = self.client.get("/api/produtos/missing")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["error"]["code"], "product_not_found")

    def test_delivery_fees_and_dates(self):
        self.assertEqual(self.client.get("/api/entrega/97201").json()["fee_cents"], 600)
        self.assertEqual(self.client.get("/api/entrega/97206").json()["fee_cents"], 900)
        self.assertEqual(self.client.get("/api/entrega/10001").status_code, 422)
        dates = self.client.get("/api/produtos/wild-at-heart/datas").json()
        self.assertEqual(len(dates), 29)
        self.assertFalse(dates[0]["available"])
        self.assertTrue(next(item for item in dates if item["date"] == "2026-11-10")["available"])

    def test_order_creation_server_totals_location_and_lookup(self):
        response = self.client.post("/api/pedidos", json={"items": [self.item]})
        self.assertEqual(response.status_code, 201, response.text)
        order = response.json()
        self.assertEqual(response.headers["location"], f"/api/pedidos/{order['id']}")
        self.assertEqual(order["status"], "recebido")
        self.assertEqual(order["currency"], "USD")
        self.assertEqual(order["subtotal_cents"], 17200)
        self.assertEqual(order["delivery_cents"], 1200)
        self.assertEqual(order["total_cents"], 18400)
        self.assertEqual(order["items"][0]["message"], "Para você <3")
        self.assertEqual(self.client.get(response.headers["location"]).json(), order)

    def test_multiple_items_and_zones(self):
        second = {**self.item, "product": "garden-party", "size": "petite", "vase": False,
                  "quantity": 1, "zip": "97206"}
        order = self.client.post("/api/pedidos", json={"items": [self.item, second]}).json()
        self.assertEqual(order["total_cents"], 25500)
        self.assertEqual(order["total_cents"], sum(item["line_total_cents"] for item in order["items"]))

    def test_custom_bouquet_persists_color_description_and_correct_total(self):
        custom = {**self.item, "product": "sunflower", "size": "abundant", "quantity": 1,
                  "vase": False, "color": "pink", "description": "Girassóis com flores de apoio rosas e papel kraft."}
        response = self.client.post("/api/pedidos", json={"items": [custom]})
        self.assertEqual(response.status_code, 201, response.text)
        order = response.json()
        self.assertEqual(order["total_cents"], 10400)
        self.assertEqual(order["items"][0]["color"], "pink")
        self.assertEqual(order["items"][0]["description"], custom["description"])
        with signed_client(create_app(self.database_path)) as restarted:
            self.assertEqual(restarted.get(f"/api/pedidos/{order['id']}").json(), order)

    def test_invalid_bouquet_customizations_are_rejected(self):
        for changes in ({"color": "blue"}, {"product": "sunflower", "color": "red"},
                        {"description": "curta"}, {"description": "x" * 1001}, {"description": None}):
            with self.subTest(changes=changes):
                response = self.client.post("/api/pedidos", json={"items": [{**self.item, **changes}]})
                self.assertEqual(response.status_code, 422, response.text)
        self.assertEqual(self.client.get("/api/pedidos").json()["total"], 0)

    def test_existing_database_gains_customization_fields_without_losing_orders(self):
        order = self.create_order()
        with self.app.state.database.connect() as connection:
            connection.execute("ALTER TABLE order_items DROP COLUMN color")
            connection.execute("ALTER TABLE order_items DROP COLUMN description")
        with signed_client(create_app(self.database_path)) as upgraded:
            self.assertEqual(upgraded.get(f"/api/pedidos/{order['id']}").json(), order)
        with signed_client(create_app(self.database_path)) as restarted:
            self.assertEqual(restarted.get(f"/api/pedidos/{order['id']}").json(), order)

    def test_invalid_input_is_rejected_without_saving(self):
        invalids = [
            {"quantity": 0}, {"quantity": 10}, {"quantity": True}, {"quantity": "2"},
            {"quantity": 1.5}, {"vase": "false"}, {"size": "invalid"}, {"price": 1},
            {"unit_price_cents": 1}, {"zip": "123"}, {"zip": "10001"},
            {"date": "2026-02-30"}, {"date": "2026-11-05"}, {"date": "2026-11-08"},
            {"date": "2027-01-01"}, {"message": "x" * 241}, {"message": None},
        ]
        for changes in invalids:
            with self.subTest(changes=changes):
                response = self.client.post("/api/pedidos", json={"items": [{**self.item, **changes}]})
                self.assertEqual(response.status_code, 422, response.text)
        self.assertEqual(self.client.get("/api/pedidos").json()["total"], 0)

    def test_empty_oversized_or_extra_order_fields_rejected(self):
        for payload in ({"items": []}, {"items": [self.item] * 31},
                        {"items": [self.item], "total_cents": 1}, {}, {"items": None}):
            self.assertEqual(self.client.post("/api/pedidos", json=payload).status_code, 422)
        response = self.client.post("/api/pedidos", content="{not json", headers={"Content-Type": "application/json"})
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["error"]["code"], "validation_error")

    def test_invalid_second_item_rolls_back_entire_order(self):
        response = self.client.post("/api/pedidos", json={"items": [self.item, {**self.item, "product": "missing"}]})
        self.assertEqual(response.status_code, 404)
        with self.app.state.database.connect() as connection:
            self.assertEqual(connection.execute("SELECT count(*) FROM orders").fetchone()[0], 0)
            self.assertEqual(connection.execute("SELECT count(*) FROM order_items").fetchone()[0], 0)

    def test_snapshot_and_persistence_across_application_restart(self):
        order = self.create_order()
        with self.app.state.database.connect() as connection:
            connection.execute("UPDATE products SET price_cents = 9900 WHERE id = ?", (self.item["product"],))
        with signed_client(create_app(self.database_path)) as another:
            self.assertEqual(another.get(f"/api/pedidos/{order['id']}").json(), order)
            self.assertEqual(another.get("/api/produtos/sunday-morning").json()["price_cents"], 9900)
            self.assertEqual(len(another.get("/api/produtos").json()), 5)
            self.assertEqual(another.post("/api/pedidos", json={"items": [self.item]}).json()["total_cents"], 28600)

    def test_catalog_localization_preserves_prices_and_existing_orders(self):
        with self.app.state.database.connect() as connection:
            connection.execute("UPDATE products SET name = 'Sunday Morning', price_cents = 9900 WHERE id = ?",
                               (self.item["product"],))
        order = self.create_order()
        self.assertEqual(order["items"][0]["product_name"], "Sunday Morning")
        with signed_client(create_app(self.database_path)) as restarted:
            product = restarted.get("/api/produtos/sunday-morning").json()
            self.assertEqual(product["name"], "Manhã de Domingo")
            self.assertEqual(product["price_cents"], 9900)
            self.assertEqual(restarted.get(f"/api/pedidos/{order['id']}").json(), order)

    def test_application_instances_keep_their_own_database(self):
        order = self.create_order()
        other_path = Path(self.directory.name) / "other.sqlite3"
        with signed_client(create_app(other_path)) as other:
            self.assertEqual(other.get("/api/pedidos").json()["total"], 0)
            self.assertEqual(other.get(f"/api/pedidos/{order['id']}").status_code, 404)
            other_order = other.post("/api/pedidos", json={"items": [self.item]}).json()
            self.assertEqual(self.client.get("/api/pedidos").json()["total"], 1)
            self.assertEqual(self.client.get(f"/api/pedidos/{other_order['id']}").status_code, 404)
            self.assertEqual(self.client.get(f"/api/pedidos/{order['id']}").json(), order)

    def test_status_lifecycle_and_terminal_states(self):
        order = self.create_order()
        path = f"/api/pedidos/{order['id']}/status"
        self.assertEqual(self.client.patch(path, json={"status": "entregue"}).status_code, 409)
        self.assertEqual(self.client.patch(path, json={"status": "recebido"}).json(), order)
        for status in ("em_preparacao", "enviado", "entregue"):
            response = self.client.patch(path, json={"status": status})
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(response.json()["status"], status)
        self.assertEqual(self.client.patch(path, json={"status": "cancelado"}).status_code, 409)
        self.assertEqual(self.client.patch(path, json={"status": "recebido"}).status_code, 409)

    def test_cancellation_before_shipping_only(self):
        for status in ("recebido", "em_preparacao", "enviado"):
            order = self.create_order()
            path = f"/api/pedidos/{order['id']}/status"
            if status != "recebido":
                self.client.patch(path, json={"status": "em_preparacao"})
            if status == "enviado":
                self.client.patch(path, json={"status": "enviado"})
            response = self.client.patch(path, json={"status": "cancelado"})
            self.assertEqual(response.status_code, 409 if status == "enviado" else 200)
            if response.status_code == 200:
                self.assertEqual(self.client.patch(path, json={"status": "em_preparacao"}).status_code, 409)

    def test_order_list_pagination_and_status_filter(self):
        first = self.create_order()
        self.create_order()
        self.client.patch(f"/api/pedidos/{first['id']}/status", json={"status": "cancelado"})
        page = self.client.get("/api/pedidos?limit=1").json()
        self.assertEqual(page["total"], 2)
        self.assertEqual(len(page["items"]), 1)
        second_page = self.client.get("/api/pedidos?limit=1&offset=1").json()
        self.assertNotEqual(page["items"][0]["id"], second_page["items"][0]["id"])
        self.assertEqual(self.client.get("/api/pedidos?status=cancelado").json()["items"][0]["id"], first["id"])
        for query in ("limit=101", "offset=-1", "status=invalid"):
            self.assertEqual(self.client.get("/api/pedidos?" + query).status_code, 422)

    def test_missing_and_malformed_order_ids(self):
        order_id = str(uuid4())
        self.assertEqual(self.client.get(f"/api/pedidos/{order_id}").status_code, 404)
        self.assertEqual(self.client.patch(f"/api/pedidos/{order_id}/status", json={"status": "cancelado"}).status_code, 404)
        self.assertEqual(self.client.get("/api/pedidos/invalid").status_code, 422)

    def test_openapi_client_and_storefront(self):
        schema = self.client.get("/openapi.json").json()
        self.assertIn("/api/pedidos/{order_id}/status", schema["paths"])
        self.assertIn("OrderCreate", schema["components"]["schemas"])
        self.assertEqual(self.client.get("/docs").status_code, 200)
        self.assertIn('src="/cliente.js"', self.client.get("/cliente").text)
        self.assertIn("fetch(", self.client.get("/auth-api.js").text)
        self.assertIn("Petal", self.client.get("/").text)
        self.assertEqual(self.client.get("/backend/data/store.sqlite3").status_code, 404)

    def test_cors_allows_local_frontend_only(self):
        headers = {"Origin": "http://127.0.0.1:4173", "Access-Control-Request-Method": "POST",
                   "Access-Control-Request-Headers": "content-type"}
        response = self.client.options("/api/pedidos", headers=headers)
        self.assertEqual(response.headers["access-control-allow-origin"], headers["Origin"])
        response = self.client.get("/api/produtos", headers={"Origin": "https://example.org"})
        self.assertNotIn("access-control-allow-origin", response.headers)

    def test_date_capacity_and_preparation_rules(self):
        self.assertIn("lotada", date_reason("2026-11-12", 2, date(2026, 11, 2)))
        self.assertIn("5 dias", date_reason("2026-11-07", 5, date(2026, 11, 5)))
        self.assertIn("válida", date_reason("2026-02-30", 2, date(2026, 11, 5)))


if __name__ == "__main__":
    unittest.main()
