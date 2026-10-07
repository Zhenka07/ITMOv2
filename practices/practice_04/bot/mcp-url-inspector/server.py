#!/usr/bin/env python3
"""
MCP Server: URL Inspector for ReadAdviserBot
Проверяет доступность веб-страниц, HTTP-статус и извлекает заголовок (title).
Реализует стандартный протокол MCP (Model Context Protocol) через JSON-RPC 2.0 (stdio).
"""

import sys
import json
import re
import urllib.request
import urllib.error
import urllib.parse
from html.parser import HTMLParser

class TitleParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_title = False
        self.title = ""

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "title":
            self.in_title = True

    def handle_endtag(self, tag):
        if tag.lower() == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title += data.strip()

def inspect_url(raw_url: str, timeout: int = 5) -> dict:
    """
    Проверяет валидность URL, доступность и возвращает статус и title страницы.
    Обрабатывает любые некорректные входные данные без сбоя сервера.
    """
    if not isinstance(raw_url, str) or not raw_url.strip():
        return {
            "status": "error",
            "error_type": "INVALID_INPUT",
            "message": "URL must be a non-empty string"
        }

    raw_url = raw_url.strip()

    # Проверка длины
    if len(raw_url) > 2048:
        return {
            "status": "error",
            "error_type": "URL_TOO_LONG",
            "message": f"URL length ({len(raw_url)}) exceeds maximum limit of 2048 characters"
        }

    # Парсинг структуры URL
    parsed = urllib.parse.urlparse(raw_url)
    if parsed.scheme not in ("http", "https"):
        return {
            "status": "error",
            "error_type": "UNSUPPORTED_SCHEME",
            "message": f"Invalid scheme '{parsed.scheme}'. Only 'http' and 'https' are allowed."
        }

    if not parsed.netloc:
        return {
            "status": "error",
            "error_type": "MISSING_HOSTNAME",
            "message": "URL is missing a valid hostname"
        }

    # Проверка на недопустимые хосты (local/private)
    forbidden_hosts = ["localhost", "127.0.0.1", "0.0.0.0", "::1"]
    hostname = parsed.hostname or ""
    if hostname.lower() in forbidden_hosts:
        return {
            "status": "error",
            "error_type": "FORBIDDEN_HOST",
            "message": f"Host '{hostname}' is not allowed for security reasons"
        }

    req = urllib.request.Request(
        raw_url,
        headers={"User-Agent": "ReadAdviserBot-UrlInspector/1.0"}
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            status_code = response.getcode()
            content_type = response.headers.get_content_type()
            final_url = response.geturl()

            title = ""
            if "html" in content_type:
                # Читаем первые 32KB для поиска title
                chunk = response.read(32768).decode("utf-8", errors="replace")
                parser = TitleParser()
                parser.feed(chunk)
                title = parser.title

            return {
                "status": "success",
                "reachable": True,
                "status_code": status_code,
                "content_type": content_type,
                "title": title or "No title found",
                "original_url": raw_url,
                "final_url": final_url
            }

    except urllib.error.HTTPError as e:
        return {
            "status": "error",
            "error_type": "HTTP_ERROR",
            "status_code": e.code,
            "message": f"Remote server returned HTTP {e.code}: {e.reason}",
            "reachable": False
        }
    except urllib.error.URLError as e:
        return {
            "status": "error",
            "error_type": "CONNECTION_FAILED",
            "message": f"Connection failed: {str(e.reason)}",
            "reachable": False
        }
    except TimeoutError:
        return {
            "status": "error",
            "error_type": "TIMEOUT",
            "message": f"Request timed out after {timeout} seconds",
            "reachable": False
        }
    except Exception as e:
        return {
            "status": "error",
            "error_type": "UNEXPECTED_ERROR",
            "message": str(e),
            "reachable": False
        }

def handle_jsonrpc_request(req: dict) -> dict:
    method = req.get("method")
    req_id = req.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "serverInfo": {
                    "name": "url-inspector-mcp",
                    "version": "1.0.0"
                }
            }
        }

    elif method == "notifications/initialized":
        return None

    elif method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "tools": [
                    {
                        "name": "inspect_url",
                        "description": "Проверяет валидность и доступность веб-ссылки, возвращает HTTP статус и title страницы",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "url": {
                                    "type": "string",
                                    "description": "URL-адрес для проверки (http или https)"
                                },
                                "timeout": {
                                    "type": "integer",
                                    "description": "Таймаут запроса в секундах (по умолчанию 5)"
                                }
                            },
                            "required": ["url"]
                        }
                    }
                ]
            }
        }

    elif method == "tools/call":
        params = req.get("params", {})
        tool_name = params.get("name")
        args = params.get("arguments", {})

        if tool_name == "inspect_url":
            url_to_test = args.get("url", "")
            timeout = args.get("timeout", 5)
            result = inspect_url(url_to_test, timeout)
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
                    "isError": result.get("status") == "error"
                }
            }
        else:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {
                    "code": -32601,
                    "message": f"Tool '{tool_name}' not found"
                }
            }

    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {
            "code": -32601,
            "message": f"Method '{method}' not found"
        }
    }

def main():
    # Если запущен с аргументом проверки
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("Testing valid URL:")
        print(json.dumps(inspect_url("https://example.com"), indent=2))
        print("\nTesting invalid scheme:")
        print(json.dumps(inspect_url("ftp://example.com"), indent=2))
        print("\nTesting invalid host:")
        print(json.dumps(inspect_url("http://localhost/secret"), indent=2))
        print("\nTesting non-existent domain:")
        print(json.dumps(inspect_url("https://non-existent-domain-123454321.org"), indent=2))
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
            err_resp = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {str(e)}"}
            }
            sys.stdout.write(json.dumps(err_resp) + "\n")
            sys.stdout.flush()

if __name__ == "__main__":
    main()
