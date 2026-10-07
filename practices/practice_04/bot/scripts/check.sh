#!/bin/bash
set -e

echo "=== 1. Checking formatting and static analysis (vet) ==="
go vet ./...

echo "=== 2. Running unit tests ==="
go test -v ./...

echo "=== 3. Compiling binary ==="
CGO_ENABLED=1 go build -o /dev/null main.go

echo "=== All checks PASSED successfully! ==="
