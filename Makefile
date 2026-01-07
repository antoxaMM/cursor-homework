.PHONY: install test run build up down logs restart clean help

help:
	@echo "Available commands:"
	@echo "  make install    - Install dependencies using uv"
	@echo "  make test       - Run tests with pytest"
	@echo "  make run        - Run bot locally"
	@echo "  make build      - Build Docker image"
	@echo "  make up         - Start bot in Docker"
	@echo "  make down       - Stop Docker container"
	@echo "  make logs       - Show Docker logs"
	@echo "  make restart    - Restart Docker container"
	@echo "  make clean      - Clean cache and temp files"

install:
	@echo "Installing dependencies with uv..."
	uv sync --all-extras

test:
	@echo "Running tests..."
	uv run pytest tests/ -v

run:
	@echo "Starting bot locally..."
	uv run python -m src.bot

build:
	@echo "Building Docker image..."
	docker build -t telegram-bot-llm .

up:
	@echo "Starting bot in Docker..."
	docker-compose up -d

down:
	@echo "Stopping Docker container..."
	docker-compose down

logs:
	@echo "Showing Docker logs..."
	docker-compose logs -f

restart:
	@echo "Restarting Docker container..."
	docker-compose restart

clean:
	@echo "Cleaning cache and temp files..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete

