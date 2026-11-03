"""
Thread-safe in-memory and persistent JSON storage for DataHub items.
Implements filtering, search, sorting, and export matching the Unified Contract.
"""

import threading
import json
import csv
import io
import os
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple

from .models import (
    Item,
    ValidationError,
    NotFoundError,
    ConflictError,
    VALID_SORT_FIELDS,
    VALID_SORT_ORDERS,
    VALID_EXPORT_FORMATS,
    validate_item_input,
)

class ItemStore:
    def __init__(self, storage_file: Optional[str] = None):
        self._lock = threading.RLock()
        self._items: Dict[str, Item] = {}
        self._storage_file = storage_file
        if storage_file and os.path.exists(storage_file):
            self._load()
        else:
            self._seed_default_data()

    def _seed_default_data(self):
        """Initial baseline brownfield items."""
        seed = [
            Item(
                id="itm-001",
                title="Configure OpenSpec Root Profile",
                category="engineering",
                status="active",
                description="Initialize OpenSpec CLI profile core with schema spec-driven.",
                tags=["openspec", "sdd", "setup"],
                priority=4,
                created_at="2026-10-20T10:00:00Z",
                updated_at="2026-10-20T10:00:00Z",
            ),
            Item(
                id="itm-002",
                title="Migrate CI Runner to Ubuntu 24.04",
                category="devops",
                status="active",
                description="Update GitHub Actions runners to use latest LTS images and Node 20+.",
                tags=["ci-cd", "infra", "docker"],
                priority=3,
                created_at="2026-10-21T12:30:00Z",
                updated_at="2026-10-21T12:30:00Z",
            ),
            Item(
                id="itm-003",
                title="Audit Prompt Injection Safeguards",
                category="security",
                status="pending",
                description="Perform threat modeling on LLM evaluator prompts and judge system prompt.",
                tags=["security", "red-team", "ai"],
                priority=5,
                created_at="2026-10-22T08:15:00Z",
                updated_at="2026-10-22T08:15:00Z",
            ),
            Item(
                id="itm-004",
                title="Two-Team Contract Reconciliation",
                category="product",
                status="active",
                description="Reconcile UI and Logic specifications into unified OpenAPI 3.1 contract.",
                tags=["contract", "spec-kit", "alignment"],
                priority=4,
                created_at="2026-10-23T14:45:00Z",
                updated_at="2026-10-23T14:45:00Z",
            ),
            Item(
                id="itm-005",
                title="Legacy Benchmark Telemetry Collector",
                category="analytics",
                status="archived",
                description="Deprecated batch telemetry script replaced by real-time event inspector.",
                tags=["deprecated", "metrics", "legacy"],
                priority=1,
                created_at="2026-10-15T09:00:00Z",
                updated_at="2026-10-18T18:00:00Z",
            ),
        ]
        with self._lock:
            for itm in seed:
                self._items[itm.id] = itm

    def _load(self):
        with self._lock:
            try:
                with open(self._storage_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._items = {k: Item(**v) for k, v in data.items()}
            except Exception:
                self._seed_default_data()

    def _save(self):
        if not self._storage_file:
            return
        with self._lock:
            data = {k: itm.to_dict() for k, itm in self._items.items()}
            with open(self._storage_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

    def create(self, raw_data: Dict[str, Any]) -> Item:
        clean = validate_item_input(raw_data, is_update=False)
        with self._lock:
            item_id = f"itm-{uuid.uuid4().hex[:6]}"
            now = datetime.now(timezone.utc).isoformat()
            item = Item(
                id=item_id,
                title=clean["title"],
                category=clean["category"],
                status=clean["status"],
                description=clean.get("description", ""),
                tags=clean.get("tags", []),
                priority=clean.get("priority", 1),
                metadata=clean.get("metadata", {}),
                created_at=now,
                updated_at=now,
            )
            self._items[item_id] = item
            self._save()
            return item

    def get(self, item_id: str) -> Item:
        with self._lock:
            if item_id not in self._items:
                raise NotFoundError(f"Item with id '{item_id}' not found.")
            return self._items[item_id]

    def update(self, item_id: str, raw_data: Dict[str, Any]) -> Item:
        clean = validate_item_input(raw_data, is_update=True)
        with self._lock:
            if item_id not in self._items:
                raise NotFoundError(f"Item with id '{item_id}' not found.")
            cur = self._items[item_id]
            now = datetime.now(timezone.utc).isoformat()

            if "title" in clean:
                cur.title = clean["title"]
            if "category" in clean:
                cur.category = clean["category"]
            if "status" in clean:
                cur.status = clean["status"]
            if "description" in clean:
                cur.description = clean["description"]
            if "tags" in clean:
                cur.tags = clean["tags"]
            if "priority" in clean:
                cur.priority = clean["priority"]
            if "metadata" in clean:
                cur.metadata = clean["metadata"]

            cur.updated_at = now
            self._save()
            return cur

    def delete(self, item_id: str) -> None:
        with self._lock:
            if item_id not in self._items:
                raise NotFoundError(f"Item with id '{item_id}' not found.")
            del self._items[item_id]
            self._save()

    def list_items(
        self,
        category: Optional[str] = None,
        status: Optional[str] = None,
        tag: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Item], int]:
        """Filters, sorts, and paginates items."""
        if sort_by not in VALID_SORT_FIELDS:
            raise ValidationError(f"Invalid sort_by '{sort_by}'. Allowed: {sorted(list(VALID_SORT_FIELDS))}")
        if sort_order not in VALID_SORT_ORDERS:
            raise ValidationError(f"Invalid sort_order '{sort_order}'. Allowed: {sorted(list(VALID_SORT_ORDERS))}")
        if offset < 0:
            raise ValidationError("Offset must be non-negative.")
        if limit <= 0 or limit > 100:
            raise ValidationError("Limit must be between 1 and 100.")

        with self._lock:
            results = list(self._items.values())

            # Filtering
            if category:
                results = [it for it in results if it.category.lower() == category.lower()]
            if status:
                results = [it for it in results if it.status.lower() == status.lower()]
            if tag:
                results = [it for it in results if any(t.lower() == tag.lower() for t in it.tags)]
            if search:
                term = search.lower().strip()
                results = [
                    it for it in results
                    if term in it.title.lower() or term in it.description.lower() or any(term in t for t in it.tags)
                ]

            total_count = len(results)

            # Sorting
            reverse = (sort_order == "desc")
            if sort_by == "priority":
                results.sort(key=lambda x: x.priority, reverse=reverse)
            elif sort_by == "title":
                results.sort(key=lambda x: x.title.lower(), reverse=reverse)
            elif sort_by == "updated_at":
                results.sort(key=lambda x: x.updated_at, reverse=reverse)
            else:  # created_at
                results.sort(key=lambda x: x.created_at, reverse=reverse)

            # Pagination
            paginated = results[offset : offset + limit]
            return paginated, total_count

    def export(
        self,
        export_format: str = "json",
        category: Optional[str] = None,
        status: Optional[str] = None,
        tag: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Tuple[str, str]:
        """Exports filtered data as JSON string or CSV string with MIME type."""
        fmt = export_format.lower()
        if fmt not in VALID_EXPORT_FORMATS:
            raise ValidationError(f"Invalid format '{export_format}'. Allowed: {sorted(list(VALID_EXPORT_FORMATS))}")

        items, _ = self.list_items(
            category=category,
            status=status,
            tag=tag,
            search=search,
            limit=100,  # export up to 100 items
        )

        if fmt == "json":
            content = json.dumps([it.to_dict() for it in items], indent=2, ensure_ascii=False)
            return content, "application/json; charset=utf-8"
        else:
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["id", "title", "category", "status", "priority", "tags", "created_at", "updated_at"])
            for it in items:
                writer.writerow([
                    it.id,
                    it.title,
                    it.category,
                    it.status,
                    it.priority,
                    ";".join(it.tags),
                    it.created_at,
                    it.updated_at,
                ])
            return output.getvalue(), "text/csv; charset=utf-8"
