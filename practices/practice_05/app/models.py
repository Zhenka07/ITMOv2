"""
DataHub Models and Validation according to Unified Spec-Kit Contract.
Strict field definitions, normalization, and validation rules.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
import re
import uuid

VALID_CATEGORIES = {"engineering", "devops", "security", "product", "analytics"}
VALID_STATUSES = {"active", "pending", "archived"}
VALID_EXPORT_FORMATS = {"json", "csv"}
VALID_SORT_FIELDS = {"created_at", "updated_at", "title", "priority"}
VALID_SORT_ORDERS = {"asc", "desc"}

class ValidationError(Exception):
    def __init__(self, message: str, invalid_params: Optional[List[Dict[str, Any]]] = None):
        super().__init__(message)
        self.message = message
        self.invalid_params = invalid_params or []

class NotFoundError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

class ConflictError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

@dataclass
class Item:
    id: str
    title: str
    category: str
    status: str
    description: str = ""
    tags: List[str] = field(default_factory=list)
    priority: int = 1  # 1 (low) to 5 (critical)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

def validate_item_input(data: Dict[str, Any], is_update: bool = False) -> Dict[str, Any]:
    """Validates item input according to reconciled contract specification."""
    errors = []

    # Title validation
    if not is_update or "title" in data:
        title = data.get("title")
        if not title or not isinstance(title, str) or not title.strip():
            errors.append({"name": "title", "reason": "Title is required and cannot be empty."})
        elif len(title.strip()) < 3:
            errors.append({"name": "title", "reason": "Title must be at least 3 characters long."})
        elif len(title) > 120:
            errors.append({"name": "title", "reason": "Title cannot exceed 120 characters."})

    # Category validation
    if not is_update or "category" in data:
        cat = data.get("category")
        if not cat or cat not in VALID_CATEGORIES:
            errors.append({
                "name": "category",
                "reason": f"Category must be one of: {sorted(list(VALID_CATEGORIES))}."
            })

    # Status validation
    if not is_update or "status" in data:
        status = data.get("status")
        if status is not None and status not in VALID_STATUSES:
            errors.append({
                "name": "status",
                "reason": f"Status must be one of: {sorted(list(VALID_STATUSES))}."
            })

    # Tags validation
    if "tags" in data and data["tags"] is not None:
        tags = data["tags"]
        if not isinstance(tags, list):
            errors.append({"name": "tags", "reason": "Tags must be a list of strings."})
        else:
            for t in tags:
                if not isinstance(t, str) or not re.match(r"^[a-zA-Z0-9\-_]{1,30}$", t):
                    errors.append({
                        "name": "tags",
                        "reason": f"Invalid tag '{t}': must be alphanumeric, hyphen or underscore, 1-30 chars."
                    })
                    break

    # Priority validation
    if "priority" in data and data["priority"] is not None:
        try:
            priority = int(data["priority"])
            if not (1 <= priority <= 5):
                errors.append({"name": "priority", "reason": "Priority must be an integer between 1 and 5."})
        except (ValueError, TypeError):
            errors.append({"name": "priority", "reason": "Priority must be an integer between 1 and 5."})

    if errors:
        raise ValidationError("Request parameters failed validation checks.", invalid_params=errors)

    cleaned = dict(data)
    if "title" in cleaned and isinstance(cleaned["title"], str):
        cleaned["title"] = cleaned["title"].strip()
    if "tags" in cleaned and isinstance(cleaned["tags"], list):
        cleaned["tags"] = [t.strip().lower() for t in cleaned["tags"] if isinstance(t, str) and t.strip()]
    if "status" not in cleaned and not is_update:
        cleaned["status"] = "active"
    if "priority" in cleaned and cleaned["priority"] is not None:
        cleaned["priority"] = int(cleaned["priority"])
    elif not is_update:
        cleaned["priority"] = 1

    return cleaned
