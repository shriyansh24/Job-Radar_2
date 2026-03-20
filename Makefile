.PHONY: dev up down test lint migrate

dev:  ## Start dev environment
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

up:   ## Start production
	docker-compose up -d

down: ## Stop all
	docker-compose down

test-backend:
	cd backend && uv run pytest tests/ -v

test-frontend:
	cd frontend && npm test -- --run

test: test-backend test-frontend

lint:
	cd backend && uv run ruff check .
	cd frontend && npm run lint

migrate:
	cd backend && uv run alembic upgrade head
