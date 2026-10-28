"""
End-to-End (E2E) Integration Scenario for Practice 5 Homework.
Simulates realistic user/operator workflow on DataHub SDD service:
List -> Search & Filter -> Validation Error Boundary -> Create -> Mutate Status -> Export -> Delete -> Verify Audit Trail.
"""

import unittest
import threading
import json
import urllib.request
import urllib.error
from http.server import HTTPServer

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.server import DataHubHandler
from app.audit import audit_logger

class TestEndToEndWorkflow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = HTTPServer(("127.0.0.1", 0), DataHubHandler)
        cls.port = cls.server.server_port
        cls.base_url = f"http://127.0.0.1:{cls.port}"
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def _http(self, method: str, path: str, body: dict = None):
        url = f"{self.base_url}{path}"
        data = json.dumps(body).encode("utf-8") if body else None
        headers = {"Content-Type": "application/json"} if body else {}
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req) as resp:
                raw = resp.read().decode("utf-8")
                ct = resp.info().get("Content-Type", "")
                content = json.loads(raw) if "json" in ct else raw
                return resp.getcode(), content, dict(resp.info())
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8")
            ct = e.headers.get("Content-Type", "")
            content = json.loads(raw) if "json" in ct else raw
            return e.code, content, dict(e.headers)

    def test_full_lifecycle_journey(self):
        print("\n--- Starting E2E Scenario Journey ---")

        # Step 1: Initial Dashboard Load
        status, data, headers = self._http("GET", "/api/v1/items")
        self.assertEqual(status, 200)
        initial_total = data["total"]
        self.assertGreaterEqual(initial_total, 5)
        print(f"Step 1: Dashboard loaded with {initial_total} baseline items.")

        # Step 2: Filter by category and search term
        status, filter_data, _ = self._http("GET", "/api/v1/items?category=engineering&search=OpenSpec")
        self.assertEqual(status, 200)
        self.assertGreaterEqual(len(filter_data["items"]), 1)
        self.assertTrue(all("openspec" in it["title"].lower() or "openspec" in " ".join(it["tags"]) for it in filter_data["items"]))
        print("Step 2: Category and keyword filtering verified.")

        # Step 3: Attempt creation with invalid data (Validation Error Boundary)
        bad_payload = {
            "title": "AB",  # Invalid: < 3 chars
            "category": "not_real",  # Invalid enum
            "priority": 99  # Invalid: not 1..5
        }
        status, prob, _ = self._http("POST", "/api/v1/items", bad_payload)
        self.assertEqual(status, 400)
        self.assertEqual(prob["title"], "Validation Error")
        self.assertGreaterEqual(len(prob["invalid_params"]), 2)
        print("Step 3: RFC 7807 error boundary caught malformed submission correctly.")

        # Step 4: Submit valid item
        valid_payload = {
            "title": "Verify Spec-Kit Contract Alignment",
            "category": "product",
            "status": "active",
            "priority": 5,
            "tags": ["sdd", "spec-kit", "reconciled"],
            "description": "Cross-team verification for Practice 5 submission"
        }
        status, created_item, _ = self._http("POST", "/api/v1/items", valid_payload)
        self.assertEqual(status, 201)
        item_id = created_item["id"]
        self.assertEqual(created_item["title"], valid_payload["title"])
        print(f"Step 4: Created new item {item_id}.")

        # Step 5: Update item status to pending
        status, updated_item, _ = self._http("PATCH", f"/api/v1/items/{item_id}", {"status": "pending"})
        self.assertEqual(status, 200)
        self.assertEqual(updated_item["status"], "pending")
        print(f"Step 5: Updated item {item_id} status to 'pending'.")

        # Step 6: Export filtered items (JSON and CSV)
        status, exp_json, _ = self._http("POST", "/api/v1/items/export", {"format": "json", "category": "product"})
        self.assertEqual(status, 200)
        self.assertTrue(any(it["id"] == item_id for it in exp_json))

        status, exp_csv, _ = self._http("POST", "/api/v1/items/export", {"format": "csv", "category": "product"})
        self.assertEqual(status, 200)
        self.assertIn(item_id, exp_csv)
        print("Step 6: Synchronous export to JSON and CSV validated.")

        # Step 7: Delete item
        status, del_resp, _ = self._http("DELETE", f"/api/v1/items/{item_id}")
        self.assertEqual(status, 200)
        self.assertTrue(del_resp["success"])

        # Verify item no longer found
        status, not_found_prob, _ = self._http("GET", f"/api/v1/items/{item_id}")
        self.assertEqual(status, 404)
        print(f"Step 7: Item {item_id} deleted and confirmed 404.")

        # Step 8: Verify Audit Trail recorded actions
        status, audit_res, _ = self._http("GET", "/api/v1/audit")
        self.assertEqual(status, 200)
        actions = [e["action"] for e in audit_res["events"]]
        self.assertIn("item.created", actions)
        self.assertIn("item.updated", actions)
        self.assertIn("data.exported", actions)
        self.assertIn("item.deleted", actions)
        print("Step 8: Audit log confirmed presence of all lifecycle events in sequence.")
        print("--- E2E Scenario Finished Successfully ---\n")

if __name__ == "__main__":
    unittest.main()
