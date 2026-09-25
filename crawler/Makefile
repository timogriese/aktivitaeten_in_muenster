.DEFAULT_GOAL := help

.PHONY: help sync backend crawler crawl clean

help:
	@echo Targets:
	@echo   make sync      - Dependencies installieren (uv sync)
	@echo   make backend   - Mock-Backend starten (Port 8001)
	@echo   make crawler   - Crawler-Service starten (Port 8000)
	@echo   make crawl     - POST /crawl manuell triggern (Crawler muss laufen)
	@echo   make clean     - __pycache__-Ordner aufraeumen

sync:
	uv sync

backend:
	uv run uvicorn mock_backend.main:app --port 8001 --reload

crawler:
	uv run uvicorn app.main:app --port 8000 --reload

crawl:
	curl -s -X POST http://localhost:8000/crawl

clean:
	python -c "import pathlib, shutil; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('__pycache__') if '.venv' not in p.parts]"
