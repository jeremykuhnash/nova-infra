.PHONY: all format lint test clean help
.PHONY: docker-build docker-run docker-clean
.PHONY: frontend-build frontend-dev
.PHONY: install dev

.DEFAULT_GOAL := help

POETRY := $(shell command -v poetry 2> /dev/null)
SRC_DIRS := backend tests
FRONTEND_DIR := frontend
DOCKER_IMAGE := tf-visualizer

help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Dev:      install | all | dev | test"
	@echo "Docker:   docker-build | docker-run"
	@echo "Frontend: frontend-build | frontend-dev"

check-poetry:
ifndef POETRY
	@curl -sSL https://install.python-poetry.org | python3 -
	@echo "Poetry installed. Add to PATH: export PATH=\"$$HOME/.local/bin:\$$PATH\""
	@exit 1
endif

install: check-poetry
	@poetry install
	@cd $(FRONTEND_DIR) && npm install

all: format lint test frontend-build docker-build

format:
	@poetry run ruff format $(SRC_DIRS)
	@poetry run ruff check --fix $(SRC_DIRS)

lint:
	@poetry run ruff check $(SRC_DIRS)
	@poetry run mypy $(SRC_DIRS)

test:
	@poetry run pytest

dev:
	@poetry run python app.py

clean:
	@find . -name "__pycache__" -type d -exec rm -rf {} + || true
	@find . -name "*.pyc" -delete || true
	@rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov || true

frontend-build:
	@cd $(FRONTEND_DIR) && npm run build

frontend-dev:
	@cd $(FRONTEND_DIR) && npm start

docker-build:
	@docker build -t $(DOCKER_IMAGE) .

docker-run:
	@docker run -p 5000:5000 $(DOCKER_IMAGE)

docker-clean:
	@docker stop $$(docker ps -q --filter ancestor=$(DOCKER_IMAGE)) 2>/dev/null || true
	@docker rm $$(docker ps -aq --filter ancestor=$(DOCKER_IMAGE)) 2>/dev/null || true
	@docker rmi $(DOCKER_IMAGE) 2>/dev/null || true
