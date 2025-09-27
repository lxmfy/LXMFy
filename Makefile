.PHONY: help install install-dev build clean test lint format check docker docker-build docker-run docker-compose-build docker-compose-up docker-compose-down publish dist wheel sdist version bump-patch bump-minor bump-major dev run update

PYTHON_VERSION := 3.13
PACKAGE_NAME := lxmfy
DOCKER_IMAGE := lxmfy-test
WHEEL_BUILDER_IMAGE := lxmfy-wheel-builder

help:
	@echo "LXMFy Development Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  update           Pull latest changes from git"
	@echo "  install          Install package dependencies"
	@echo "  install-dev      Install development dependencies"
	@echo "  build            Build package using poetry"
	@echo "  wheel            Build wheel using setup.py"
	@echo "  sdist            Build source distribution"
	@echo "  dist             Build both wheel and sdist"
	@echo "  clean            Clean build artifacts"
	@echo "  test             Run tests"
	@echo "  lint             Run linting (ruff)"
	@echo "  format           Format code (ruff)"
	@echo "  check            Run safety check"
	@echo "  dev              Install in development mode"
	@echo "  run              Run echo bot for testing"
	@echo "  version          Show current version"
	@echo "  bump-patch       Bump patch version"
	@echo "  bump-minor       Bump minor version"
	@echo "  bump-major       Bump major version"
	@echo "  docker           Build and run Docker container"
	@echo "  docker-build     Build Docker image"
	@echo "  docker-run       Run Docker container"
	@echo "  docker-compose-build  Build using docker-compose"
	@echo "  docker-compose-up     Start services with docker-compose"
	@echo "  docker-compose-down   Stop services with docker-compose"
	@echo "  publish          Publish to PyPI"

update:
	git pull

install:
	poetry install

install-dev:
	poetry install --with dev
	poetry run pip install pytest pytest-asyncio pytest-cov

build:
	poetry build

wheel:
	python setup.py bdist_wheel

sdist:
	python setup.py sdist

dist: wheel sdist

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf __pycache__/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

test:
	poetry run pytest tests/ -v

lint:
	poetry run ruff check .

format:
	poetry run ruff format .

check:
	poetry run safety check

dev:
	poetry install

run:
	poetry run lxmfy run echo

version:
	@python -c "import lxmfy; print(lxmfy.__version__)"

bump-patch:
	poetry version patch
	@$(MAKE) update-version

bump-minor:
	poetry version minor
	@$(MAKE) update-version

bump-major:
	poetry version major
	@$(MAKE) update-version

update-version:
	@NEW_VERSION=$$(poetry version -s); \
	echo "__version__ = \"$$NEW_VERSION\"" > lxmfy/__version__.py; \
	echo "Updated version to $$NEW_VERSION"

docker: docker-build docker-run

docker-build:
	docker build -t $(DOCKER_IMAGE) .

docker-run:
	docker run -d \
		--name $(DOCKER_IMAGE)-bot \
		-v $$(pwd)/config:/bot/config \
		-v $$(pwd)/.reticulum:/root/.reticulum \
		--restart unless-stopped \
		$(DOCKER_IMAGE)

docker-run-host:
	docker run -d \
		--name $(DOCKER_IMAGE)-bot \
		--network host \
		-v $$(pwd)/config:/bot/config \
		-v $$(pwd)/.reticulum:/root/.reticulum \
		--restart unless-stopped \
		$(DOCKER_IMAGE)

docker-wheel-build:
	docker build -f Dockerfile.Build -t $(WHEEL_BUILDER_IMAGE) .

docker-wheel-extract:
	docker run --rm -v "$$(pwd)/dist_output:/output" $(WHEEL_BUILDER_IMAGE)

docker-compose-build:
	docker-compose build

docker-compose-up:
	docker-compose up -d

docker-compose-down:
	docker-compose down

docker-compose-logs:
	docker-compose logs -f

docker-stop:
	docker stop $(DOCKER_IMAGE)-bot || true
	docker rm $(DOCKER_IMAGE)-bot || true

docker-clean: docker-stop
	docker rmi $(DOCKER_IMAGE) || true
	docker rmi $(WHEEL_BUILDER_IMAGE) || true

publish:
	poetry publish --build

publish-test:
	poetry publish --build --repository testpypi

all: clean lint test build

ci: lint check test build
