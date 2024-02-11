SHELL := /bin/bash

lint:
	echo "Running Ruff linter..."
	ruff check .

format:
	@echo "Running Ruff formatter..."
	ruff format .
