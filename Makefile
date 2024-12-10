.PHONY: all
all: ## Show the available make targets.
	@echo "Usage: make <target>"
	@echo ""
	@echo "Targets:"
	@fgrep "##" Makefile | fgrep -v fgrep

.PHONY: clean
clean: ## Clean the temporary files.
	rm -rf .mypy_cache
	rm -rf .ruff_cache
	rm -rf .pytest_cache
	rm -rf __pycache__

.PHONY: black
black: ## Run black.
	python3 -m black . || true

.PHONY: ruff
ruff: ## Run ruff without fixing.
	python3 -m ruff check . || true

.PHONY: pylint
pylint: ## Run pylint.
	python3 -m pylint . || true

.PHONY: lint
lint:  ## Run Python linter
	make black
	make ruff
	make pylint

.PHONY: install
install:  ## Install the dependencies excluding dev.
	pip install -r requirements.txt

.PHONY: install-dev
install-dev:  ## Install the dependencies including dev.
	pip install -r dev_requirements.txt

.PHONY: run-local
run-local: ## Run lambda locally but connected to the S3 bucket
	@echo "Running lambda test..."
	python3 run_local.py
