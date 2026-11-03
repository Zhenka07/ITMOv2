"""
Automated API and Unit Test Suite for DataHub SDD Service.
Verifies all functional requirements, RFC 7807 error formats, and boundary conditions.
"""

import unittest
import threading
import json
import urllib.request
import urllib.error
import urllib.parse
from http.server import HTTPServer

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.server import DataHubHandler, store
from app.models import validate_item_input, ValidationError
from app.audit import audit_logger

class TestDataHubAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Start server in background thread on ephemeral port
        cls.server = HTTPServer(("127.0.0.1", 0), DataHubHandler)
        cls.port = cls.server.server_port
        cls.base_url = f"http://127.0.0.1:{cls.port}"
        cls.server_thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.server_thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def _request(self, method: str, path: str, data: dict = None, expected_status: int = 200):
        url = f"{self.base_url}{path}"
        body = json.dumps(data).encode("utf-8") if data else None
        headers = {"Content-Type": "application/json"} if data else {}
        req = urllib.request.Request(url, data=body, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req) as response:
                status = response.getcode()
                raw = response.read().decode("utf-8")
                resp_headers = dict(response.info())
                content = json.loads(raw) if "application/json" in resp_headers.get("Content-Type", "") else raw
                return status, content, resp_headers
        except urllib.error.HTTPError as e:
            status = e.code
            raw = e.read().decode("utf-8")
            resp_headers = dict(e.headers)
            content = json.loads(raw) if "problem+json" in resp_headers.get("Content-Type", "") or "application/json" in resp_headers.get("Content-Type", "") else raw
            return status, content, resp_headers

    # --- Scenario 1: Health & Baseline ---
    def test_health_check(self):
        status, data, _ = self._request("GET", "/api/v1/health")
        self.assertEqual(status, 200)
        self.assertEqual(data["status"], "healthy")
        self.assertIn("Spec-Kit", data["frameworks"])

    # --- Scenario 2: List & Filter Happy Path ---
    def test_list_items_and_headers(self):
        status, data, headers = self._request("GET", "/api/v1/items?category=devops")
        self.assertEqual(status, 200)
        self.assertIn("items", data)
        self.assertGreaterEqual(data["total"], 1)
        self.assertEqual(data["items"][0]["category"], "devops")
        self.assertIn("X-Total-Count", headers)

    def test_text_search(self):
        status, data, _ = self._request("GET", "/api/v1/items?search=runner")
        self.assertEqual(status, 200)
        self.assertGreaterEqual(len(data["items"]), 1)
        self.assertTrue(any("runner" in it["title"].lower() for it in data["items"]))

    # --- Scenario 3: Validation & Error Handling (RFC 7807) ---
    def test_create_item_validation_error(self):
        payload = {
            "title": "Hi",  # Too short (min 3 chars)
            "category": "invalid_category",  # Not in allowed enum
            "priority": 10  # Must be 1..5
        }
        status, data, headers = self._request("POST", "/api/v1/items", payload)
        self.assertEqual(status, 400)
        self.assertIn("application/problem+json", headers.get("Content-Type", ""))
        self.assertEqual(data["title"], "Validation Error")
        self.assertIn("invalid_params", data)
        invalid_names = [p["name"] for p in data["invalid_params"]]
        self.assertIn("title", invalid_names)
        self.assertIn("category", invalid_names)
        self.assertIn("priority", invalid_names)

    def test_not_found_error(self):
        status, data, headers = self._request("GET", "/api/v1/items/non-existent-id")
        self.assertEqual(status, 404)
        self.assertIn("application/problem+json", headers.get("Content-Type", ""))
        self.assertEqual(data["title"], "Not Found")

    # --- Scenario 4: Export Capabilities ---
    def test_export_json(self):
        payload = {"format": "json", "category": "engineering"}
        status, content, headers = self._request("POST", "/api/v1/items/export", payload)
        self.assertEqual(status, 200)
        self.assertIn("application/json", headers.get("Content-Type", ""))
        self.assertIn("attachment; filename=items_export.json", headers.get("Content-Disposition", ""))
        self.assertIsInstance(content, list)
        self.assertTrue(all(it["category"] == "engineering" for it in content))

    def test_export_csv(self):
        payload = {"format": "csv"}
        status, content, headers = self._request("POST", "/api/v1/items/export", payload)
        self.assertEqual(status, 200)
        self.assertIn("text/csv", headers.get("Content-Type", ""))
        self.assertIn("attachment; filename=items_export.csv", headers.get("Content-Disposition", ""))
        lines = content.splitlines()
        self.assertGreaterEqual(len(lines), 2)
        self.assertTrue(lines[0].startswith("id,title,category"))

    def test_export_invalid_format(self):
        payload = {"format": "xml"}
        status, data, _ = self._request("POST", "/api/v1/items/export", payload)
        self.assertEqual(status, 400)
        self.assertEqual(data["title"], "Validation Error")

    # --- Scenario 5: Audit Log Recording ---
    def test_audit_log_emission(self):
        # Create item
        item_payload = {
            "title": "Audit Verification Task",
            "category": "security",
            "status": "pending",
            "tags": ["audit", "test"]
        }
        status, created, _ = self._request("POST", "/api/v1/items", item_payload)
        self.assertEqual(status, 201)
        item_id = created["id"]

        # Check audit trail endpoint
        status, audit_data, _ = self._request("GET", "/api/v1/audit")
        self.assertEqual(status, 200)
        events = audit_data["events"]
        created_events = [e for e in events if e.get("resource_id") == item_id and e.get("action") == "item.created"]
        self.assertGreaterEqual(len(created_events), 1)

if __name__ == "__main__":
    unittest.main()
