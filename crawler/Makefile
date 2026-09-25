.DEFAULT_GOAL := help

.PHONY: help install dev mock-backend crawl lint clean

help:
	@echo Targets:
	@echo   make install       - Dependencies installieren (uv sync)
	@echo   make dev           - Crawler-Service starten (Port 8000)
	@echo   make mock-backend  - Mock-Backend starten (Port 8001)
	@echo   make crawl         - POST /crawl manuell triggern (Crawler muss laufen)
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

lint:
	uv run ruff check .

clean:
	python -c "import pathlib, shutil; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('__pycache__') if '.venv' not in p.parts]"
