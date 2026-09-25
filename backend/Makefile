.DEFAULT_GOAL := help

.PHONY: help install dev lint

# Paths are relative to backend/ - spring-boot:run uses it as the working directory.
# The SQLite file sits at the repo root so it can be committed and shared.
export DATABASE_PATH = ../activities.db
export ROUTING_OSM_FILE = data/muenster-regbez-260924.osm.pbf
export ROUTING_GRAPH_DIRECTORY = data/graph

help:
	@echo Targets:
	@echo   make install   - Dependencies laden + kompilieren (mvn compile)
	@echo   make dev       - Backend starten (Port 8080)
	@echo   make lint      - Kompilier-Check (kein Java-Linter konfiguriert)
	@echo OSM-Extrakt fuers Routing erwartet unter backend/data/, siehe README.md.

install:
	mvn -q -DskipTests compile

dev:
	mvn spring-boot:run

lint:
	mvn -q -DskipTests compile
