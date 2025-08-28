.PHONY: help install install-dev lint format test clean train collect start groups docker-build docker-run

# Default target
help:
	@echo "GroupMe Anti-Spam Bot - Available commands:"
	@echo ""
	@echo "Development:"
	@echo "  install      Install the package in development mode"
	@echo "  install-dev  Install development dependencies"
	@echo "  lint         Run linting checks"
	@echo "  format       Format code with black"
	@echo "  test         Run tests"
	@echo "  clean        Clean build artifacts"
	@echo ""
	@echo "Bot operations:"
	@echo "  train        Train the spam detection model"
	@echo "  collect      Collect training data (set GROUP_ID=123456789)"
	@echo "  start        Start the bot (set GROUP_ID=123456789)"
	@echo "  groups       List available groups"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build Build Docker image"
	@echo "  docker-run   Run bot in Docker (set GROUP_ID=123456789)"
	@echo ""
	@echo "Examples:"
	@echo "  make start GROUP_ID=123456789"
	@echo "  make collect GROUP_ID=123456789"
	@echo "  make train"

# Development
install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"
	pip install black ruff mypy pytest

lint:
	ruff check groupme_bot/
	ruff check tests/

format:
	black groupme_bot/
	black tests/

test:
	pytest tests/ -v

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

# Bot operations
train:
	python -m groupme_bot.cli train

collect:
	@if [ -z "$(GROUP_ID)" ]; then \
		echo "Error: GROUP_ID is required. Use: make collect GROUP_ID=123456789"; \
		exit 1; \
	fi
	python -m groupme_bot.cli collect --group-id $(GROUP_ID)

start:
	@if [ -z "$(GROUP_ID)" ]; then \
		echo "Error: GROUP_ID is required. Use: make start GROUP_ID=123456789"; \
		exit 1; \
	fi
	python -m groupme_bot.cli start --group-id $(GROUP_ID)

groups:
	python -m groupme_bot.cli groups

# Docker
docker-build:
	docker build -t groupme-anti-spam-bot .

docker-run:
	@if [ -z "$(GROUP_ID)" ]; then \
		echo "Error: GROUP_ID is required. Use: make docker-run GROUP_ID=123456789"; \
		exit 1; \
	fi
	docker run --rm \
		-e API_KEY \
		-e BOT_USER_ID \
		-v $(PWD)/data:/app/data \
		groupme-anti-spam-bot start --group-id $(GROUP_ID)
