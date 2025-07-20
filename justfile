# justfile for Cogency - beautiful, simple, and effective.
# Default command: list all commands
default:
    @just --list

# --- DEVELOPMENT ---

# Install all dependencies
install:
    @echo "Installing Python dependencies..."
    @poetry install

# Run all tests
test: test-python

# Run Python tests
test-python:
    @echo "Running Python tests..."
    @poetry run pytest tests/

# --- QUALITY ---

# Format code with ruff
format:
    @echo "Formatting Python code with ruff..."
    @poetry run ruff format .

# Lint code with ruff
lint:
    @echo "Linting Python code with ruff..."
    @poetry run ruff check .

# Fix linting issues with ruff
fix:
    @echo "Fixing Python linting issues with ruff..."
    @poetry run ruff check . --fix

# --- DISTRIBUTION ---

# Build the Python package
build:
    @echo "Building Python package..."
    @poetry build

# Publish the Python package to PyPI
publish:
    @echo "Publishing Python package to PyPI..."
    @poetry publish

# --- MISCELLANEOUS ---

# Clean build artifacts
clean:
    @echo "Cleaning build artifacts..."
    @rm -rf dist build .pytest_cache .mypy_cache .ruff_cache

# Show recent commits
commits:
    @git --no-pager log --pretty=format:"%ar %s"