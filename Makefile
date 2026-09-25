.DEFAULT_GOAL := help

.PHONY: help install lint dev crawl backend crawler frontend mock-backend

help:
	@echo Globales Makefile - jeder Bereich (backend, crawler, frontend) hat dieselben
	@echo Targets install/dev/lint in seinem eigenen Makefile; dieses hier ruft sie auf.
	@echo Targets:
	@echo   make install      - Dependencies in allen Bereichen installieren
	@echo   make lint         - Linting in allen Bereichen
	@echo   make dev          - Backend (8080), Crawler (8000) und Frontend (3000) zusammen starten
	@echo   make crawl        - Einen Crawl-Zyklus ausloesen (zweites Terminal, waehrend make dev laeuft)
	@echo   make backend      - nur Backend starten
	@echo   make crawler      - nur Crawler starten
	@echo   make frontend     - nur Frontend starten
	@echo   make mock-backend - Python-Mock statt Spring-Backend (Port 8001, fuer offline/ohne Java)
	@echo Weitere Targets je Bereich: backend\Makefile, crawler\Makefile, frontend\Makefile

install:
	$(MAKE) -C backend install
	$(MAKE) -C crawler install
	$(MAKE) -C frontend install

lint:
	$(MAKE) -C backend lint
	$(MAKE) -C crawler lint
	$(MAKE) -C frontend lint

# All three are long-running; -j runs them in parallel in this one terminal, Ctrl+C stops all.
dev:
	$(MAKE) -j3 backend crawler frontend

crawl:
	$(MAKE) -C crawler crawl

backend:
	$(MAKE) -C backend dev

crawler:
	$(MAKE) -C crawler dev

frontend:
	$(MAKE) -C frontend dev

mock-backend:
	$(MAKE) -C crawler mock-backend
