.PHONY: up down logs test

up:
	docker-compose up -d --build

down:
	docker-compose down -v

logs:
	docker-compose logs -f api

test:
	pytest -v

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -f app.db

.DEFAULT_GOAL := help

help:
	@echo "Available commands:"
	@echo "  make up      - Start the service with Docker Compose"
	@echo "  make down    - Stop and remove containers (with volume cleanup)"
	@echo "  make logs    - View service logs"
	@echo "  make test    - Run pytest"
	@echo "  make clean   - Clean up cache and database"
