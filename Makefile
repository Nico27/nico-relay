# Developer shortcuts. Everything here is also documented in README.md.
SHELL := /bin/sh
COMPOSE := docker compose

.PHONY: help up down logs ps migrate seed test test-api test-api-all test-web shell

help:
	@printf '%s\n' \
	  'make up         dev stack (db + api hot reload + vite)' \
	  'make down       stop the dev stack' \
	  'make migrate    apply pending SQL migrations' \
	  'make seed       reload seed.sql (destructive)' \
	  'make test       backend + frontend tests' \
	  'make logs       tail the dev stack logs'

up:
	$(COMPOSE) up --build

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f --tail=100

ps:
	$(COMPOSE) ps

migrate:
	$(COMPOSE) exec -T api python -m relay.migrate

seed:
	$(COMPOSE) exec -T api python -m relay.seed --reset --seed /app/seed.sql

test: test-api test-web

test-api:
	cd backend && uv run pytest -q

test-api-all:
	cd backend && TEST_DATABASE_URL=postgresql://relay:relay@localhost:55432/relay uv run pytest -q

test-web:
	cd frontend && npm run typecheck && npm test

shell:
	$(COMPOSE) exec api sh
