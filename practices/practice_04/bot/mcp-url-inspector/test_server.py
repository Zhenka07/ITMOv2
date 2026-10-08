#!/usr/bin/env python3
"""
Unit and Integration Tests for MCP URL Inspector Server.
"""

import unittest
import json
import subprocess
import sys
import os
from unittest.mock import patch, MagicMock
import urllib.error

# Импортируем тестируемый модуль
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import server

class TestTitleParser(unittest.TestCase):
    def test_extract_standard_title(self):
        parser = server.TitleParser()
        parser.feed("<html><head><title>Test Article</title></head><body>Hello</body></html>")
        self.assertEqual(parser.title, "Test Article")

    def test_extract_case_insensitive_title(self):
        parser = server.TitleParser()
        parser.feed("<html><head><TITLE>Uppercase Title</TITLE></head></html>")
        self.assertEqual(parser.title, "Uppercase Title")

    def test_html_without_title(self):
        parser = server.TitleParser()
        parser.feed("<html><body><p>No title here</p></body></html>")
        self.assertEqual(parser.title, "")


class TestURLValidation(unittest.TestCase):
    def test_empty_and_non_string_input(self):
        res1 = server.inspect_url("")
        self.assertEqual(res1["status"], "error")
        self.assertEqual(res1["error_type"], "INVALID_INPUT")

        res2 = server.inspect_url(None)
        self.assertEqual(res2["status"], "error")
        self.assertEqual(res2["error_type"], "INVALID_INPUT")

    def test_unsupported_schemes(self):
        schemes = ["ftp://example.com/file", "file:///etc/passwd", "javascript:alert(1)"]
        for s in schemes:
            res = server.inspect_url(s)
            self.assertEqual(res["status"], "error", f"Scheme in '{s}' should fail")
            self.assertEqual(res["error_type"], "UNSUPPORTED_SCHEME")

    def test_url_too_long(self):
        long_url = "https://example.com/" + ("a" * 2050)
        res = server.inspect_url(long_url)
        self.assertEqual(res["status"], "error")
        self.assertEqual(res["error_type"], "URL_TOO_LONG")

    def test_ssrf_forbidden_hosts(self):
        forbidden = [
            "http://localhost/admin",
            "http://127.0.0.1:8080/metrics",
            "https://0.0.0.0/",
            "http://[::1]:3000"
        ]
        for url in forbidden:
            res = server.inspect_url(url)
            self.assertEqual(res["status"], "error", f"Host in '{url}' should be forbidden")
            self.assertEqual(res["error_type"], "FORBIDDEN_HOST")


class TestNetworkInspection(unittest.TestCase):
    @patch("urllib.request.urlopen")
    def test_successful_http_fetch(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.getcode.return_value = 200
        mock_resp.headers.get_content_type.return_value = "text/html"
        mock_resp.geturl.return_value = "https://example.com/final"
        mock_resp.read.return_value = b"<html><head><title>Mocked Page</title></head></html>"
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        res = server.inspect_url("https://example.com/start")
        self.assertEqual(res["status"], "success")
        self.assertTrue(res["reachable"])
        self.assertEqual(res["status_code"], 200)
        self.assertEqual(res["title"], "Mocked Page")
        self.assertEqual(res["final_url"], "https://example.com/final")

    @patch("urllib.request.urlopen")
    def test_http_404_error_handling(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="https://example.com/404",
            code=404,
            msg="Not Found",
            hdrs={},
            fp=None
        )

        res = server.inspect_url("https://example.com/404")
        self.assertEqual(res["status"], "error")
        self.assertEqual(res["error_type"], "HTTP_ERROR")
        self.assertEqual(res["status_code"], 404)
        self.assertFalse(res["reachable"])

    @patch("urllib.request.urlopen")
    def test_connection_error_handling(self, mock_urlopen):
        mock_urlopen.side_effect = urllib.error.URLError(reason="Name or service not known")

        res = server.inspect_url("https://non-existent-domain-404.org")
        self.assertEqual(res["status"], "error")
        self.assertEqual(res["error_type"], "CONNECTION_FAILED")
        self.assertFalse(res["reachable"])

    @patch("urllib.request.urlopen")
    def test_timeout_error_handling(self, mock_urlopen):
        mock_urlopen.side_effect = TimeoutError("Timed out")

        res = server.inspect_url("https://timeout.example.com", timeout=1)
        self.assertEqual(res["status"], "error")
        self.assertEqual(res["error_type"], "TIMEOUT")
        self.assertFalse(res["reachable"])


class TestJSONRPCProtocol(unittest.TestCase):
    def test_initialize_request(self):
        req = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
        resp = server.handle_jsonrpc_request(req)
        self.assertEqual(resp["jsonrpc"], "2.0")
        self.assertEqual(resp["id"], 1)
        self.assertIn("capabilities", resp["result"])
        self.assertEqual(resp["result"]["serverInfo"]["name"], "url-inspector-mcp")

    def test_tools_list_request(self):
        req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
        resp = server.handle_jsonrpc_request(req)
        tools = resp["result"]["tools"]
        self.assertEqual(len(tools), 1)
        self.assertEqual(tools[0]["name"], "inspect_url")
        self.assertIn("inputSchema", tools[0])
        self.assertIn("url", tools[0]["inputSchema"]["properties"])

    def test_tools_call_valid_url(self):
        with patch.object(server, "inspect_url", return_value={"status": "success", "status_code": 200, "title": "OK"}):
            req = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {"name": "inspect_url", "arguments": {"url": "https://example.com"}}
            }
            resp = server.handle_jsonrpc_request(req)
            self.assertFalse(resp["result"]["isError"])
            content = json.loads(resp["result"]["content"][0]["text"])
            self.assertEqual(content["status"], "success")

    def test_tools_call_invalid_url(self):
        req = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {"name": "inspect_url", "arguments": {"url": "ftp://example.com"}}
        }
        resp = server.handle_jsonrpc_request(req)
        self.assertTrue(resp["result"]["isError"])
        content = json.loads(resp["result"]["content"][0]["text"])
        self.assertEqual(content["status"], "error")
        self.assertEqual(content["error_type"], "UNSUPPORTED_SCHEME")

    def test_unknown_method(self):
        req = {"jsonrpc": "2.0", "id": 99, "method": "unknown/method", "params": {}}
        resp = server.handle_jsonrpc_request(req)
        self.assertIn("error", resp)
        self.assertEqual(resp["error"]["code"], -32601)


class TestStdioEndToEnd(unittest.TestCase):
    """Тест реального запуска server.py через подпроцесс stdio"""
    def test_server_process_communication(self):
        proc = subprocess.Popen(
            [sys.executable, os.path.join(os.path.dirname(__file__), "server.py")],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        try:
            # 1. Отправляем initialize
            init_req = json.dumps({"jsonrpc": "2.0", "id": 10, "method": "initialize"})
            proc.stdin.write(init_req + "\n")
            proc.stdin.flush()
            init_resp = json.loads(proc.stdout.readline())
            self.assertEqual(init_resp["id"], 10)

            # 2. Отправляем битый JSON (Parse Error -32700)
            proc.stdin.write("{invalid_json\n")
            proc.stdin.flush()
            err_resp = json.loads(proc.stdout.readline())
            self.assertEqual(err_resp["error"]["code"], -32700)

        finally:
            if proc.stdin:
                proc.stdin.close()
            if proc.stdout:
                proc.stdout.close()
            if proc.stderr:
                proc.stderr.close()
            proc.terminate()
            proc.wait()


if __name__ == "__main__":
    unittest.main()
