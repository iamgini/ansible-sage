# Ansible Sage - Makefile for common development tasks

.PHONY: help install install-dev test lint format clean docker-build docker-up docker-down run docs

# Default target
.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)Ansible Sage - Development Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

# ============================================================================
# Installation
# ============================================================================

install: ## Install production dependencies
	pip install -r requirements.txt

install-dev: ## Install development dependencies
	pip install -r requirements.txt -r requirements-dev.txt
	pre-commit install

# ============================================================================
# Development
# ============================================================================

run: ## Run the API server locally
	uvicorn sage.api.server:app --reload --host 0.0.0.0 --port 8000

run-prod: ## Run the API server in production mode
	uvicorn sage.api.server:app --host 0.0.0.0 --port 8000 --workers 4

# ============================================================================
# Testing
# ============================================================================

test: ## Run all tests
	pytest

test-unit: ## Run unit tests only
	pytest tests/unit/ -v

test-integration: ## Run integration tests
	pytest tests/integration/ -v -m integration

test-cov: ## Run tests with coverage report
	pytest --cov=sage --cov-report=html --cov-report=term
	@echo "$(GREEN)Coverage report generated in htmlcov/index.html$(NC)"

test-watch: ## Run tests in watch mode
	pytest-watch -- -v

# ============================================================================
# Code Quality
# ============================================================================

lint: ## Run all linters
	@echo "$(BLUE)Running ruff...$(NC)"
	ruff check sage/ tests/
	@echo "$(BLUE)Running mypy...$(NC)"
	mypy sage/
	@echo "$(BLUE)Running bandit...$(NC)"
	bandit -r sage/

format: ## Format code with black and isort
	@echo "$(BLUE)Running black...$(NC)"
	black sage/ tests/
	@echo "$(BLUE)Running isort...$(NC)"
	isort sage/ tests/
	@echo "$(GREEN)Code formatted!$(NC)"

check: format lint test-unit ## Run format, lint, and unit tests

pre-commit: ## Run pre-commit hooks on all files
	pre-commit run --all-files

# ============================================================================
# Docker
# ============================================================================

docker-build: ## Build Docker image
	docker build -t ansible-sage:latest .

docker-up: ## Start all services with docker-compose
	docker-compose up -d

docker-down: ## Stop all services
	docker-compose down

docker-logs: ## Show logs from all containers
	docker-compose logs -f

docker-restart: ## Restart the ansible-sage service
	docker-compose restart ansible-sage

docker-rebuild: ## Rebuild and restart services
	docker-compose up -d --build

docker-shell: ## Open shell in ansible-sage container
	docker-compose exec ansible-sage bash

docker-test: ## Run tests in Docker container
	docker-compose exec ansible-sage pytest

# ============================================================================
# Database
# ============================================================================

db-migrate: ## Run database migrations
	alembic upgrade head

db-rollback: ## Rollback last database migration
	alembic downgrade -1

db-reset: ## Reset database (WARNING: destroys data)
	docker-compose exec postgres psql -U sage -d ansible_sage -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
	$(MAKE) db-migrate

# ============================================================================
# Cleanup
# ============================================================================

clean: ## Clean up generated files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	rm -rf dist/ build/ 2>/dev/null || true
	@echo "$(GREEN)Cleanup complete!$(NC)"

clean-all: clean ## Clean everything including Docker volumes
	docker-compose down -v
	rm -rf logs/* generated_playbooks/*

# ============================================================================
# Documentation
# ============================================================================

docs: ## Build documentation
	cd docs && mkdocs build

docs-serve: ## Serve documentation locally
	cd docs && mkdocs serve

# ============================================================================
# Utilities
# ============================================================================

env-check: ## Check required environment variables
	@echo "$(BLUE)Checking environment...$(NC)"
	@python -c "import os; missing = [v for v in ['ANTHROPIC_API_KEY', 'DATABASE_URL', 'REDIS_URL'] if not os.getenv(v)]; print('$(RED)Missing:$(NC)', missing) if missing else print('$(GREEN)All required vars set$(NC)')"

version: ## Show current version
	@python -c "import sage; print(sage.__version__)"

deps-update: ## Update dependencies
	pip install --upgrade pip
	pip install --upgrade -r requirements.txt -r requirements-dev.txt

safety-check: ## Check for security vulnerabilities
	safety check -r requirements.txt
