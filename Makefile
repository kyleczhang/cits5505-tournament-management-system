SHELL := /bin/bash

APP_DIR := app
VENV := $(APP_DIR)/.venv
PYTHON := $(VENV)/bin/python
PIP := $(PYTHON) -m pip
FLASK := cd $(APP_DIR) && .venv/bin/flask --app run:app
PYTEST := cd $(APP_DIR) && .venv/bin/python -m pytest

.DEFAULT_GOAL := run

.PHONY: help venv install install-dev env setup setup-dev run test test-unit test-selenium db-upgrade db-migrate seed seed-reset clean

help:
	@printf "Available targets:\n"
	@printf "  make venv           Create app/.venv\n"
	@printf "  make install        Install runtime dependencies\n"
	@printf "  make install-dev    Install development dependencies\n"
	@printf "  make env            Copy app/.env.example to app/.env if missing\n"
	@printf "  make setup          venv + runtime deps + .env bootstrap + db upgrade\n"
	@printf "  make setup-dev      venv + dev deps + .env bootstrap + db upgrade\n"
	@printf "  make run            Run the Flask dev server\n"
	@printf "  make test           Run the full test suite\n"
	@printf "  make test-unit      Run unit tests only\n"
	@printf "  make test-selenium  Run Selenium tests only\n"
	@printf "  make db-upgrade     Apply Alembic migrations\n"
	@printf "  make db-migrate     Create a migration (use MSG=\"...\")\n"
	@printf "  make seed           Seed demo data\n"
	@printf "  make seed-reset     Reset and re-seed demo data\n"
	@printf "  make clean          Remove Python cache files\n"

venv:
	@test -x "$(PYTHON)" || python3 -m venv "$(VENV)"

install: venv
	$(PIP) install -r $(APP_DIR)/requirements.txt

install-dev: venv
	$(PIP) install -r $(APP_DIR)/requirements-dev.txt

env:
	@test -f $(APP_DIR)/.env || cp $(APP_DIR)/.env.example $(APP_DIR)/.env

setup: install env db-upgrade

setup-dev: install-dev env db-upgrade

run:
	$(FLASK) run

test:
	$(PYTEST) tests -q

test-unit:
	$(PYTEST) tests/unit -q

test-selenium:
	$(PYTEST) tests/selenium -q

db-upgrade:
	$(FLASK) db upgrade

db-migrate:
	@if [ -z "$(MSG)" ]; then echo 'Usage: make db-migrate MSG="describe change"'; exit 1; fi
	@$(FLASK) db migrate -m "$(MSG)"

seed:
	$(FLASK) seed

seed-reset:
	$(FLASK) seed --reset

clean:
	@find $(APP_DIR) -type d -name __pycache__ -prune -exec rm -rf {} +
	@find $(APP_DIR) -type f -name '*.pyc' -delete
