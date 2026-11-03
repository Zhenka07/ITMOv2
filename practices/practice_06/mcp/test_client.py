#!/usr/bin/env python3
"""
Test client for Mini Shop AppSec Auditor MCP Server.
Tests JSON-RPC 2.0 handshake, tool discovery, and tool execution.
"""

import subprocess
import json
import sys
import os

def test_mcp():
    server_path = os.path.join(os.path.dirname(__file__), "security_auditor.py")
    proc = subprocess.Popen(
        [sys.executable, server_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    def exchange(msg):
        proc.stdin.write(json.dumps(msg) + "\n")
        proc.stdin.flush()
        line = proc.stdout.readline()
        return json.loads(line)

    print("1. Handshake initialize...")
    r1 = exchange({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "test"}}
    })
    assert r1["id"] == 1
    assert r1["result"]["serverInfo"]["name"] == "minishop-appsec-auditor"
    print("✓ Initialized successfully")

    print("2. Listing tools...")
    r2 = exchange({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
    tools = [t["name"] for t in r2["result"]["tools"]]
    assert "evaluate_threat_model" in tools
    assert "test_role_spoofing" in tools
    print(f"✓ Discovered {len(tools)} tools: {', '.join(tools)}")

    print("3. Executing evaluate_threat_model...")
    r3 = exchange({
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {"name": "evaluate_threat_model", "arguments": {}}
    })
    res_text = r3["result"]["content"][0]["text"]
    data = json.loads(res_text)
    assert data["status"] == "success"
    assert data["verdict"] == "APPROVED"
    print(f"✓ Threat model evaluated: score = {data['score']}/10, verdict = {data['verdict']}")

    proc.terminate()
    print("\nAll MCP JSON-RPC protocol tests completed successfully!")

if __name__ == "__main__":
    test_mcp()
