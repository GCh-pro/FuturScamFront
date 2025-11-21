.PHONY: help install run run-reload dev test test-api clean lint format

help:
	@echo "FuturScam API - Makefile Commands"
	@echo "===================================="
	@echo ""
	@echo "Available commands:"
	@echo "  make install        - Install dependencies from requirements.txt"
	@echo "  make run            - Run API in production mode (port 8000)"
	@echo "  make run-reload     - Run API in development mode with auto-reload"
	@echo "  make dev            - Alias for run-reload"
	@echo "  make test-api       - Test API endpoints with test_api.py"
	@echo "  make test           - Run tests"
	@echo "  make clean          - Remove cache and compiled files"
	@echo "  make lint           - Run code linter (pylint)"
	@echo "  make format         - Format code with black"
	@echo ""

install:
	pip install -r requirements.txt
	python -m spacy download en_core_web_sm

run:
	uvicorn main:app --host 0.0.0.0 --port 8000

run-reload:
	uvicorn main:app --reload --host 127.0.0.1 --port 8000

dev: run-reload

test-api:
	python test_api.py

test:
	pytest -v

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +

lint:
	pylint main.py params.py test.py

format:
	black main.py params.py test.py
