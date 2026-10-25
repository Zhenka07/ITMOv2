#!/usr/bin/env python3
"""
Test client to verify MCP JSON-RPC protocol over stdio for url-inspector.
"""

import subprocess
import json
import sys

def run_mcp_session():
    proc = subprocess.Popen(
        [sys.executable, "mcp-url-inspector/server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    requests = [
        # 1. Initialize
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"capabilities": {}}
        },
        # 2. List tools
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        },
        # 3. Call tool: SUCCESS scenario
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "inspect_url",
                "arguments": {
                    "url": "https://example.com"
                }
            }
        },
        # 4. Call tool: ERROR scenario 1 (invalid scheme)
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "inspect_url",
                "arguments": {
                    "url": "ftp://files.example.com"
                }
            }
        },
        # 5. Call tool: ERROR scenario 2 (forbidden host)
        {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "inspect_url",
                "arguments": {
                    "url": "http://127.0.0.1:8080/admin"
                }
            }
        }
    ]

    print("=== STARTING MCP JSON-RPC PROTOCOL TEST ===\n")
    for req in requests:
        req_line = json.dumps(req)
        print(f">> CLIENT REQUEST (method: {req.get('method')}):")
        print(json.dumps(req, indent=2))
        proc.stdin.write(req_line + "\n")
        proc.stdin.flush()

        resp_line = proc.stdout.readline()
        if resp_line:
            resp = json.loads(resp_line.strip())
            print(f"<< SERVER RESPONSE (id: {resp.get('id')}):")
            print(json.dumps(resp, ensure_ascii=False, indent=2))
        print("-" * 50)

    proc.terminate()
    print("=== MCP TEST FINISHED SUCCESSFULLY ===")

if __name__ == "__main__":
    run_mcp_session()
