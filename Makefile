.DEFAULT_GOAL := help

.PHONY: help install lint frontend crawler mock-backend backend

help:
	@echo Globales Makefile - jeder Bereich (crawler, frontend, backend) hat dieselben
	@echo Targets install/dev/lint in seinem eigenen Makefile; dieses hier startet/
	@echo installiert/lintet sie von der Repo-Wurzel aus.
	@echo Targets:
	@echo   make install      - Dependencies in allen Bereichen installieren
	@echo   make lint         - Linting in allen Bereichen
	@echo   make frontend     - Frontend Dev-Server starten (Nuxt, Port 3000)
	@echo   make crawler      - Crawler-Service starten (Port 8000)
	@echo   make mock-backend - Mock-Backend starten (Port 8001, bis Spring-Boot-Backend steht)
	@echo   make backend      - Spring-Boot-Backend starten (folgt, sobald backend/ steht)
	@echo Weitere Targets je Bereich: crawler\Makefile, frontend\Makefile

install:
	$(MAKE) -C crawler install
	$(MAKE) -C frontend install

lint:
	$(MAKE) -C crawler lint
	$(MAKE) -C frontend lint

frontend:
	$(MAKE) -C frontend dev

crawler:
	$(MAKE) -C crawler dev

mock-backend:
	$(MAKE) -C crawler mock-backend

backend:
	@echo backend/ ist noch nicht befuellt - Spring-Boot-Setup vom Kollegen steht noch aus.
	@echo Sobald da: backend/Makefile mit install/dev/lint-Targets ergaenzen (gleiches
	@echo Schema wie crawler/frontend) und hier per "make -C backend dev" einbinden -
	@echo dann auch in "make install"/"make lint" oben mitnehmen.
