.DEFAULT_GOAL := help

.PHONY: help install dev mock-backend crawl crawl-bulk lint clean

RUNS ?= 10

help:
	@echo Targets:
	@echo   make install       - Dependencies installieren (uv sync)
	@echo   make dev           - Crawler-Service starten (Port 8000)
	@echo   make mock-backend  - Mock-Backend starten (Port 8001)
	@echo   make crawl         - POST /crawl manuell triggern (Crawler muss laufen)
	@echo   make crawl-bulk    - RUNS Crawl-Zyklen nacheinander (Default 10, je 5 Tavily-Credits)
	@echo   make lint          - Linting (ruff)
	@echo   make clean         - __pycache__-Ordner aufraeumen

install:
	uv sync

dev:
	uv run uvicorn app.main:app --port 8000 --reload

mock-backend:
	uv run uvicorn mock_backend.main:app --port 8001 --reload

crawl:
	curl -s -X POST http://localhost:8000/crawl

crawl-bulk:
	uv run python -c "import httpx; [print(httpx.post('http://localhost:8000/crawl', timeout=900).text, flush=True) for _ in range($(RUNS))]"

lint:
	uv run ruff check .

clean:
	python -c "import pathlib, shutil; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('__pycache__') if '.venv' not in p.parts]"
