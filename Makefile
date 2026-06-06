.DEFAULT_GOAL := help

.PHONY: help install run-backend run-frontend run-all test lint format type-check pre-commit clean

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependencies (backend + frontend)
	cd backend && pip install -r requirements.txt
	cd frontend && pip install -r requirements.txt
	pre-commit install

run-backend: ## Start the FastAPI backend (uvicorn, hot-reload)
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run-frontend: ## Start the Streamlit frontend
	cd frontend && streamlit run app.py --server.port 8501

run-all: ## Start backend and frontend concurrently
	$(MAKE) run-backend & $(MAKE) run-frontend

test: ## Run the test suite
	cd backend && pytest tests/ -v

lint: ## Lint with ruff
	ruff check backend/ frontend/

format: ## Format with ruff
	ruff format backend/ frontend/

type-check: ## Type-check with mypy
	mypy backend/app

pre-commit: ## Run all pre-commit hooks against all files
	pre-commit run --all-files

clean: ## Remove build artifacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
