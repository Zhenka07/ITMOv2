#!/usr/bin/env python3
"""
Model Context Protocol (MCP) Server: DataHub SDD Inspector.
Implements the standard MCP JSON-RPC 2.0 stdio protocol.
Enables AI coding agents and human operators to query DataHub records,
execute contract validations, perform data exports, and audit operations.
"""

import sys
import os
import json
from typing import Dict, Any, Optional

# Add parent directory to path so we can import app modules directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.storage import ItemStore
from app.models import ValidationError, NotFoundError, ConflictError
from app.audit import audit_logger

# Persistent or memory store
store = ItemStore(os.path.join(os.path.dirname(__file__), "..", "app", "data.json"))

SERVER_INFO = {
    "name": "datahub-sdd-inspector",
    "version": "1.0.0",
}

AVAILABLE_TOOLS = [
    {
        "name": "list_items",
        "description": "Lists items from DataHub with optional filtering by category, status, search query, and sorting.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": ["engineering", "devops", "security", "product", "analytics"],
                    "description": "Filter by item category"
                },
                "status": {
                    "type": "string",
                    "enum": ["active", "pending", "archived"],
                    "description": "Filter by lifecycle status"
                },
                "search": {
                    "type": "string",
                    "description": "Substring search term across title, description, and tags"
                },
                "sort_by": {
                    "type": "string",
                    "enum": ["created_at", "updated_at", "title", "priority"],
                    "default": "created_at"
                },
                "sort_order": {
                    "type": "string",
                    "enum": ["asc", "desc"],
                    "default": "desc"
                },
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 100,
                    "default": 20
                },
                "offset": {
                    "type": "integer",
                    "minimum": 0,
                    "default": 0
                }
            }
        }
    },
    {
        "name": "get_item",
        "description": "Retrieves full details of a specific item by its unique ID (e.g. 'itm-001').",
        "inputSchema": {
            "type": "object",
            "required": ["item_id"],
            "properties": {
                "item_id": {
                    "type": "string",
                    "description": "Item identifier"
                }
            }
        }
    },
    {
        "name": "create_item",
        "description": "Creates a new item adhering to the unified Spec-Kit contract schema.",
        "inputSchema": {
            "type": "object",
            "required": ["title", "category"],
            "properties": {
                "title": {"type": "string", "minLength": 3, "maxLength": 120},
                "category": {
                    "type": "string",
                    "enum": ["engineering", "devops", "security", "product", "analytics"]
                },
                "status": {"type": "string", "enum": ["active", "pending", "archived"], "default": "active"},
                "priority": {"type": "integer", "minimum": 1, "maximum": 5, "default": 1},
                "tags": {"type": "array", "items": {"type": "string"}},
                "description": {"type": "string"}
            }
        }
    },
    {
        "name": "update_item_status",
        "description": "Updates the status of an existing item ('active', 'pending', or 'archived').",
        "inputSchema": {
            "type": "object",
            "required": ["item_id", "status"],
            "properties": {
                "item_id": {"type": "string"},
                "status": {"type": "string", "enum": ["active", "pending", "archived"]}
            }
        }
    },
    {
        "name": "export_items",
        "description": "Exports filtered items in either JSON or RFC 4180 CSV format.",
        "inputSchema": {
            "type": "object",
            "required": ["format"],
            "properties": {
                "format": {"type": "string", "enum": ["json", "csv"]},
                "category": {"type": "string"},
                "status": {"type": "string"},
                "search": {"type": "string"}
            }
        }
    },
    {
        "name": "get_audit_events",
        "description": "Retrieves the recent immutable audit events for state mutations.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "default": 20}
            }
        }
    }
]

def execute_tool(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Executes a tool and returns structured result or error message."""
    try:
        if name == "list_items":
            items, total = store.list_items(
                category=arguments.get("category"),
                status=arguments.get("status"),
                search=arguments.get("search"),
                sort_by=arguments.get("sort_by", "created_at"),
                sort_order=arguments.get("sort_order", "desc"),
                offset=arguments.get("offset", 0),
                limit=arguments.get("limit", 20),
            )
            return {
                "status": "success",
                "total": total,
                "count": len(items),
                "items": [it.to_dict() for it in items],
            }

        elif name == "get_item":
            item_id = arguments.get("item_id")
            if not item_id:
                return {"status": "error", "error": "item_id parameter is required"}
            item = store.get(item_id)
            return {"status": "success", "item": item.to_dict()}

        elif name == "create_item":
            item = store.create(arguments)
            audit_logger.record_event(
                action="item.created",
                actor="mcp-client",
                resource_id=item.id,
                details={"title": item.title, "category": item.category}
            )
            return {"status": "success", "item": item.to_dict()}

        elif name == "update_item_status":
            item_id = arguments.get("item_id")
            status = arguments.get("status")
            if not item_id or not status:
                return {"status": "error", "error": "item_id and status are required"}
            updated = store.update(item_id, {"status": status})
            audit_logger.record_event(
                action="item.updated",
                actor="mcp-client",
                resource_id=item_id,
                details={"status": status}
            )
            return {"status": "success", "item": updated.to_dict()}

        elif name == "export_items":
            fmt = arguments.get("format", "json")
            content, mime = store.export(
                export_format=fmt,
                category=arguments.get("category"),
                status=arguments.get("status"),
                search=arguments.get("search")
            )
            audit_logger.record_event(
                action="data.exported",
                actor="mcp-client",
                details={"format": fmt}
            )
            return {
                "status": "success",
                "format": fmt,
                "mime_type": mime,
                "content": content
            }

        elif name == "get_audit_events":
            limit = arguments.get("limit", 20)
            events = audit_logger.list_events(limit=limit)
            return {"status": "success", "events": events, "count": len(events)}

        else:
            return {"status": "error", "error": f"Unknown tool: '{name}'"}

    except ValidationError as ve:
        return {
            "status": "error",
            "error_type": "RFC7807_VALIDATION_ERROR",
            "message": ve.message,
            "invalid_params": ve.invalid_params
        }
    except NotFoundError as ne:
        return {"status": "error", "error_type": "NOT_FOUND", "message": ne.message}
    except Exception as e:
        return {"status": "error", "error_type": "INTERNAL_ERROR", "message": str(e)}

def handle_jsonrpc_request(req: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    req_id = req.get("id")
    method = req.get("method")
    params = req.get("params", {})

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": SERVER_INFO,
            }
        }

    elif method == "notifications/initialized":
        return None

    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {"tools": AVAILABLE_TOOLS}
        }

    elif method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        result = execute_tool(tool_name, arguments)
        is_error = result.get("status") == "error"

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, ensure_ascii=False, indent=2)
                    }
                ],
                "isError": is_error
            }
        }

    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": -32601, "message": f"Method '{method}' not found"}
    }

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("Testing MCP Tools...")
        # 1. list_items
        res = execute_tool("list_items", {"category": "devops"})
        print("list_items (devops):", json.dumps(res, indent=2))
        assert res["status"] == "success"
        # 2. validation error
        bad_res = execute_tool("create_item", {"title": "X", "category": "unknown"})
        print("create_item (validation error):", json.dumps(bad_res, indent=2))
        assert bad_res["status"] == "error"
        assert len(bad_res["invalid_params"]) >= 1
        # 3. export_items
        csv_res = execute_tool("export_items", {"format": "csv"})
        print("export_items (csv head):", csv_res["content"].splitlines()[0])
        assert "text/csv" in csv_res["mime_type"]
        print("All MCP self-tests passed successfully!")
        return

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            resp = handle_jsonrpc_request(req)
            if resp is not None:
                sys.stdout.write(json.dumps(resp) + "\n")
                sys.stdout.flush()
        except Exception as e:
            err = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {str(e)}"}
            }
            sys.stdout.write(json.dumps(err) + "\n")
            sys.stdout.flush()

if __name__ == "__main__":
    main()
