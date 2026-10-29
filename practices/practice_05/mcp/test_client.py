#!/usr/bin/env python3
"""
Integration test client for DataHub SDD MCP Server.
Tests JSON-RPC 2.0 handshake, tool discovery, execution, and error handling.
"""

import subprocess
import json
import sys
import os

def run_mcp_session():
    server_path = os.path.join(os.path.dirname(__file__), "server.py")
    proc = subprocess.Popen(
        [sys.executable, server_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    def send_recv(msg):
        proc.stdin.write(json.dumps(msg) + "\n")
        proc.stdin.flush()
        line = proc.stdout.readline()
        return json.loads(line)

    print("1. Testing initialize handshake...")
    init_req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-agent", "version": "1.0"}
        }
    }
    resp = send_recv(init_req)
    assert resp["id"] == 1
    assert resp["result"]["serverInfo"]["name"] == "datahub-sdd-inspector"
    print("✓ Initialize successful")

    print("2. Testing tools/list...")
    tools_req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
    resp = send_recv(tools_req)
    assert resp["id"] == 2
    tools = resp["result"]["tools"]
    tool_names = [t["name"] for t in tools]
    assert "list_items" in tool_names
    assert "create_item" in tool_names
    assert "export_items" in tool_names
    print(f"✓ Discovered {len(tools)} tools: {', '.join(tool_names)}")

    print("3. Testing tools/call: list_items...")
    call_req = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "list_items",
            "arguments": {"category": "security"}
        }
    }
    resp = send_recv(call_req)
    assert resp["id"] == 3
    content_raw = resp["result"]["content"][0]["text"]
    data = json.loads(content_raw)
    assert data["status"] == "success"
    print(f"✓ list_items returned {data['count']} items")

    print("4. Testing tools/call: create_item with validation error...")
    bad_req = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "create_item",
            "arguments": {"title": "ab", "category": "invalid_cat"}
        }
    }
    resp = send_recv(bad_req)
    assert resp["id"] == 4
    assert resp["result"]["isError"] is True
    err_data = json.loads(resp["result"]["content"][0]["text"])
    assert err_data["error_type"] == "RFC7807_VALIDATION_ERROR"
    print("✓ Validation error handled gracefully with structured problem details")

    print("5. Testing tools/call: export_items...")
    export_req = {
        "jsonrpc": "2.0",
        "id": 5,
        "method": "tools/call",
        "params": {
            "name": "export_items",
            "arguments": {"format": "json"}
        }
    }
    resp = send_recv(export_req)
    assert resp["id"] == 5
    exp_data = json.loads(resp["result"]["content"][0]["text"])
    assert exp_data["format"] == "json"
    print("✓ export_items generated valid JSON payload")

    proc.terminate()
    print("\nAll MCP JSON-RPC protocol tests completed successfully!")

if __name__ == "__main__":
    run_mcp_session()
