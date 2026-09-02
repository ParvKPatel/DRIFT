.PHONY: help dev-backend dev-frontend db-up db-down test lint clean

help:
	@echo "OIL SENTINEL - Development Commands"
	@echo "-----------------------------------"
	@echo "make db-up         - Start PostgreSQL with pgvector container"
	@echo "make db-down       - Stop PostgreSQL container"
	@echo "make dev-backend   - Run FastAPI backend locally"
	@echo "make dev-frontend  - Run Next.js frontend locally"
	@echo "make test-backend  - Run backend pytest suite"
	@echo "make lint-frontend - Run frontend type check and linter"
	@echo "make clean         - Clean cache directories"

db-up:
	docker-compose up -d postgres

db-down:
	docker-compose down

dev-backend:
	cd backend && uvicorn app.main:app --reload --port 8000

dev-frontend:
	cd frontend && npm run dev

test-backend:
	cd backend && pytest -v

lint-frontend:
	cd frontend && npm run lint && npx tsc --noEmit

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	rm -rf frontend/.next
