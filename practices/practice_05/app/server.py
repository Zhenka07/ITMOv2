"""
DataHub REST API and UI Server.
Conforms strictly to the Unified Contract (OpenAPI 3.1 & RFC 7807 Problem Details).
Includes live Web UI dashboard serving at root.
"""

import sys
import os
import json
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any, Optional

from .models import ValidationError, NotFoundError, ConflictError
from .storage import ItemStore
from .audit import audit_logger

# Global singleton or configurable store
DEFAULT_STORAGE_FILE = os.path.join(os.path.dirname(__file__), "data.json")
store = ItemStore(DEFAULT_STORAGE_FILE)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

class DataHubHandler(BaseHTTPRequestHandler):
    server_version = "DataHub-SDD/1.0"

    def _send_problem(self, status: int, title: str, detail: str, type_suffix: str, invalid_params: Optional[list] = None):
        payload = {
            "type": f"https://api.datahub.local/errors/{type_suffix}",
            "title": title,
            "status": status,
            "detail": detail,
            "instance": self.path,
        }
        if invalid_params:
            payload["invalid_params"] = invalid_params

        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/problem+json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Request-ID")
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, status: int, data: Any, headers: Optional[Dict[str, str]] = None):
        body = json.dumps(data, indent=2, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Request-ID")
        if headers:
            for k, v in headers.items():
                self.send_header(k, str(v))
        self.end_headers()
        self.wfile.write(body)

    def _read_json_body(self) -> Dict[str, Any]:
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length <= 0:
            return {}
        raw = self.rfile.read(content_length).decode("utf-8")
        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON payload in request body: {str(e)}")

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Request-ID")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # Static assets or UI
        if path == "/" or path == "/index.html" or path.startswith("/static"):
            self._serve_static(path)
            return

        # Health endpoint
        if path == "/api/v1/health":
            self._send_json(200, {
                "status": "healthy",
                "service": "DataHub-SDD",
                "version": "1.0.0",
                "frameworks": ["OpenSpec", "Spec-Kit"],
            })
            return

        # Audit events endpoint
        if path == "/api/v1/audit":
            events = audit_logger.list_events()
            self._send_json(200, {"events": events, "total": len(events)})
            return

        # Specs info
        if path == "/api/v1/specs":
            spec_path = os.path.join(os.path.dirname(__file__), "..", "spec-kit", "contract", "unified_contract.yaml")
            contract_available = os.path.exists(spec_path)
            self._send_json(200, {
                "contract": "OpenAPI 3.1.0",
                "unified_schema": "spec-kit/contract/unified_contract.yaml",
                "available": contract_available,
            })
            return

        # List items
        if path == "/api/v1/items":
            try:
                category = query.get("category", [None])[0]
                status = query.get("status", [None])[0]
                tag = query.get("tag", [None])[0]
                search = query.get("search", [None])[0]
                sort_by = query.get("sort_by", ["created_at"])[0]
                sort_order = query.get("sort_order", ["desc"])[0]
                offset = int(query.get("offset", [0])[0])
                limit = int(query.get("limit", [20])[0])

                items, total = store.list_items(
                    category=category,
                    status=status,
                    tag=tag,
                    search=search,
                    sort_by=sort_by,
                    sort_order=sort_order,
                    offset=offset,
                    limit=limit,
                )
                headers = {
                    "X-Total-Count": total,
                    "X-Offset": offset,
                    "X-Limit": limit,
                }
                self._send_json(200, {
                    "items": [it.to_dict() for it in items],
                    "total": total,
                    "offset": offset,
                    "limit": limit,
                }, headers=headers)
            except ValidationError as ve:
                self._send_problem(400, "Validation Error", ve.message, "validation-error", ve.invalid_params)
            except Exception as e:
                self._send_problem(500, "Internal Server Error", str(e), "server-error")
            return

        # Get item by ID
        if path.startswith("/api/v1/items/"):
            item_id = path[len("/api/v1/items/"):]
            if "/" in item_id:
                self._send_problem(404, "Not Found", f"Endpoint {path} not found.", "not-found")
                return
            try:
                item = store.get(item_id)
                self._send_json(200, item.to_dict())
            except NotFoundError as ne:
                self._send_problem(404, "Not Found", ne.message, "resource-not-found")
            except Exception as e:
                self._send_problem(500, "Internal Server Error", str(e), "server-error")
            return

        # 404 for any other path
        self._send_problem(404, "Not Found", f"Resource '{path}' does not exist.", "not-found")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # Export items
        if path == "/api/v1/items/export":
            try:
                body = self._read_json_body()
                fmt = body.get("format", "json")
                category = body.get("category")
                status = body.get("status")
                tag = body.get("tag")
                search = body.get("search")

                content, content_type = store.export(
                    export_format=fmt,
                    category=category,
                    status=status,
                    tag=tag,
                    search=search,
                )
                audit_logger.record_event(
                    action="data.exported",
                    actor=self.client_address[0],
                    details={"format": fmt, "category": category, "status": status}
                )
                raw_bytes = content.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(raw_bytes)))
                self.send_header("Content-Disposition", f"attachment; filename=items_export.{fmt}")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(raw_bytes)
            except ValidationError as ve:
                self._send_problem(400, "Validation Error", ve.message, "validation-error", ve.invalid_params)
            except Exception as e:
                self._send_problem(500, "Internal Server Error", str(e), "server-error")
            return

        # Create item
        if path == "/api/v1/items":
            try:
                body = self._read_json_body()
                item = store.create(body)
                audit_logger.record_event(
                    action="item.created",
                    actor=self.client_address[0],
                    resource_id=item.id,
                    details={"title": item.title, "category": item.category}
                )
                self._send_json(201, item.to_dict())
            except ValidationError as ve:
                self._send_problem(400, "Validation Error", ve.message, "validation-error", ve.invalid_params)
            except ConflictError as ce:
                self._send_problem(409, "Conflict", ce.message, "conflict")
            except Exception as e:
                self._send_problem(500, "Internal Server Error", str(e), "server-error")
            return

        self._send_problem(404, "Not Found", f"Endpoint '{path}' not found.", "not-found")

    def do_PATCH(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path.startswith("/api/v1/items/"):
            item_id = path[len("/api/v1/items/"):]
            try:
                body = self._read_json_body()
                updated = store.update(item_id, body)
                audit_logger.record_event(
                    action="item.updated",
                    actor=self.client_address[0],
                    resource_id=item_id,
                    details={"updated_fields": list(body.keys())}
                )
                self._send_json(200, updated.to_dict())
            except NotFoundError as ne:
                self._send_problem(404, "Not Found", ne.message, "resource-not-found")
            except ValidationError as ve:
                self._send_problem(400, "Validation Error", ve.message, "validation-error", ve.invalid_params)
            except Exception as e:
                self._send_problem(500, "Internal Server Error", str(e), "server-error")
            return

        self._send_problem(404, "Not Found", f"Endpoint '{path}' not found.", "not-found")

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path.startswith("/api/v1/items/"):
            item_id = path[len("/api/v1/items/"):]
            try:
                store.delete(item_id)
                audit_logger.record_event(
                    action="item.deleted",
                    actor=self.client_address[0],
                    resource_id=item_id,
                )
                self._send_json(200, {"success": True, "message": f"Item {item_id} deleted."})
            except NotFoundError as ne:
                self._send_problem(404, "Not Found", ne.message, "resource-not-found")
            except Exception as e:
                self._send_problem(500, "Internal Server Error", str(e), "server-error")
            return

        self._send_problem(404, "Not Found", f"Endpoint '{path}' not found.", "not-found")

    def _serve_static(self, path: str):
        if path == "/" or path == "/index.html":
            file_path = os.path.join(STATIC_DIR, "index.html")
            content_type = "text/html; charset=utf-8"
        else:
            rel = path[len("/static/"):] if path.startswith("/static/") else path.lstrip("/")
            file_path = os.path.join(STATIC_DIR, rel)
            if file_path.endswith(".css"):
                content_type = "text/css; charset=utf-8"
            elif file_path.endswith(".js"):
                content_type = "application/javascript; charset=utf-8"
            elif file_path.endswith(".png"):
                content_type = "image/png"
            elif file_path.endswith(".json"):
                content_type = "application/json; charset=utf-8"
            else:
                content_type = "text/plain; charset=utf-8"

        if not os.path.exists(file_path):
            self._send_problem(404, "Static File Not Found", f"Static file '{path}' was not found on server.", "not-found")
            return

        with open(file_path, "rb") as f:
            content = f.read()

        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format, *args):
        # Concise logging
        if os.environ.get("DATAHUB_DEBUG") == "1":
            super().log_message(format, *args)

def run_server(port: int = 8080, host: str = "0.0.0.0"):
    server_address = (host, port)
    httpd = HTTPServer(server_address, DataHubHandler)
    print(f"DataHub SDD Server running at http://{host}:{port}/")
    print(f"Web Dashboard UI: http://localhost:{port}/")
    print(f"API Health Endpoint: http://localhost:{port}/api/v1/health")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server gracefully...")
        httpd.server_close()

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    run_server(port=port)
