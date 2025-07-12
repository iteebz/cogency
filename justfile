# justfile
# Common commands for the multi-language Cogency repository

# Build commands
build-python:
    @echo "Building Python package..."
    cd python && poetry build

build-js:
    @echo "Building JavaScript package..."
    cd js && npm install && npm run build

build-all: build-python build-js
    @echo "All packages built."

# Test commands
test-python:
    @echo "Running Python tests..."
    cd python && poetry run pytest

test-js:
    @echo "Running JavaScript tests..."
    cd js && npm test

test: test-python
test-all: test-python test-js
    @echo "All tests passed."

# Publish commands (requires proper authentication/configuration)
publish-python:
    @echo "Publishing Python package to PyPI..."
    cd python && poetry publish

publish-js:
    @echo "Publishing JavaScript package to NPM..."
    cd js && npm publish

# Version syncing (placeholder - implement scripts/sync_versions.py)
sync-versions:
    @echo "Syncing versions between Python and JS packages..."
    @python scripts/sync_versions.py || echo "Warning: scripts/sync_versions.py not found or failed. Please implement it."

# Formatting and Linting
format-python:
    @echo "Formatting Python code with ruff..."
    cd python && poetry run ruff format .

lint-python:
    @echo "Linting Python code with ruff..."
    cd python && poetry run ruff check .

fix-python:
    @echo "Fixing Python linting issues with ruff..."
    cd python && poetry run ruff check . --fix

format: format-python
lint: lint-python
fix: fix-python

# Clean commands
clean-python:
    @echo "Cleaning Python build artifacts..."
    cd python && rm -rf dist build .pytest_cache .mypy_cache .ruff_cache

clean-js:
    @echo "Cleaning JavaScript build artifacts..."
    cd js && rm -rf dist node_modules

clean-all: clean-python clean-js
    @echo "All build artifacts cleaned."

# Install dependencies
install-python:
    @echo "Installing Python dependencies..."
    cd python && poetry install

install-js:
    @echo "Installing JavaScript dependencies..."
    cd js && npm install

install-all: install-python install-js
    @echo "All dependencies installed."

commits:
    @git --no-pager log --pretty=format:"%ar %s"
