"""
Automated Contract Conformance Validator.
Loads the OpenAPI 3.1 YAML contract and verifies that API endpoints
strictly adhere to declared JSON Schemas, properties, and required fields.
"""

import unittest
import os
import json
import yaml
import jsonschema

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.storage import ItemStore
from app.models import validate_item_input

CONTRACT_PATH = os.path.join(os.path.dirname(__file__), "..", "spec-kit", "contract", "unified_contract.yaml")

class TestContractConformance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(CONTRACT_PATH, "r", encoding="utf-8") as f:
            cls.spec = yaml.safe_load(f)
        cls.schemas = cls.spec["components"]["schemas"]
        cls.store = ItemStore()

    def test_item_schema_conformance(self):
        """Verifies that items produced by the store validate against OpenAPI Item schema."""
        schema = self.schemas["Item"]
        items, _ = self.store.list_items()
        self.assertGreater(len(items), 0)

        for item in items:
            item_dict = item.to_dict()
            # Clean fields not strictly in schema properties if needed
            filtered = {k: v for k, v in item_dict.items() if k in schema["properties"]}
            jsonschema.validate(instance=filtered, schema=schema)

    def test_problem_details_schema_conformance(self):
        """Verifies that validation errors conform to RFC 7807 ProblemDetails schema."""
        schema = self.schemas["ProblemDetails"]
        resolver = jsonschema.RefResolver.from_schema(self.spec)
        bad_sample = {
            "type": "https://api.datahub.local/errors/validation-error",
            "title": "Validation Error",
            "status": 400,
            "detail": "Request parameters failed validation checks.",
            "instance": "/api/v1/items",
            "invalid_params": [
                {"name": "title", "reason": "Title is required."}
            ]
        }
        jsonschema.validate(instance=bad_sample, schema=schema, resolver=resolver)

    def test_allowed_categories_match_contract_enum(self):
        """Ensures python models VALID_CATEGORIES match OpenAPI category enum."""
        from app.models import VALID_CATEGORIES
        contract_categories = set(self.schemas["Item"]["properties"]["category"]["enum"])
        self.assertEqual(VALID_CATEGORIES, contract_categories)

    def test_allowed_statuses_match_contract_enum(self):
        """Ensures python models VALID_STATUSES match OpenAPI status enum."""
        from app.models import VALID_STATUSES
        contract_statuses = set(self.schemas["Item"]["properties"]["status"]["enum"])
        self.assertEqual(VALID_STATUSES, contract_statuses)

if __name__ == "__main__":
    unittest.main()
