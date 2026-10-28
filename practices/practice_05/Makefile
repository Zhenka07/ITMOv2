.PHONY: run test mcp-test validate clean

PYTHON ?= python3

run:
	$(PYTHON) -m app.server 8080

test:
	$(PYTHON) -m unittest discover -s tests

mcp-test:
	$(PYTHON) mcp/test_client.py

validate:
	cd openspec && openspec validate --strict

clean:
	rm -f app/*.pyc tests/*.pyc mcp/*.pyc
	find . -type d -name "__pycache__" -exec rm -rf {} +
