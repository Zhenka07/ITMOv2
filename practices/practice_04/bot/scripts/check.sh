#!/bin/sh
set -e

# Автоматически переходим в корень проекта бота, независимо от места вызова
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$BOT_DIR"

echo "Working directory: $BOT_DIR"

echo "=== 1. Checking formatting and static analysis (vet) ==="
go vet ./...

echo "=== 2. Running Go unit tests (TDD features) ==="
go test -v ./...

echo "=== 3. Running Skill verification tests ==="
python3 .opencode/skills/test_skill.py

echo "=== 4. Running MCP server test suite ==="
python3 -m unittest mcp-url-inspector/test_server.py

echo "=== 5. Compiling binary ==="
CGO_ENABLED=1 go build -o /dev/null main.go

echo "=== All checks PASSED successfully! ==="
