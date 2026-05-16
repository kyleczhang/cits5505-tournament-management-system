SHELL := /bin/bash

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(PYTHON) -m pip
FLASK := .venv/bin/flask --app run:app
PYTEST := .venv/bin/python -m pytest

.DEFAULT_GOAL := run

.PHONY: help venv install install-dev env setup setup-dev run test test-unit test-selenium db-upgrade db-migrate seed seed-reset clean

help:
	@printf "Available targets:\n"
	@printf "  make venv           Create .venv\n"
	@printf "  make install        Install runtime dependencies\n"
	@printf "  make install-dev    Install development dependencies\n"
	@printf "  make env            Copy .env.example to .env if missing\n"
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
	$(PIP) install -r requirements.txt

install-dev: venv
	$(PIP) install -r requirements-dev.txt

env:
	@test -f .env || cp .env.example .env

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
	@find . -type d -name __pycache__ -prune -exec rm -rf {} +
	@find . -type f -name '*.pyc' -delete
