# Cogency - A beautiful, simple, and effective justfile
# Default command: list all commands
default:
    @just --list

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ⚙️  SETUP & ENVIRONMENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Install all dependencies
install:
    @echo "Installing Python dependencies..."
    @poetry install

# Create a virtual environment if it doesn't exist
venv:
    @poetry env use python3
    @echo "Virtual environment created. Activate with 'poetry shell'"

# Update all dependencies
update:
    @echo "Updating dependencies..."
    @poetry update

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🚀 DEVELOPMENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Run the MCP server
mcp-server transport="stdio":
    @echo "Starting MCP server with {{transport}} transport..."
    @poetry run python -c "import asyncio; from cogency import Agent; asyncio.run(Agent(enable_mcp=True).serve_mcp('{{transport}}'))"

# Run a specific example (hello, memory, research, coding)
example name="hello":
    @echo "Running example: {{name}}..."
    @poetry run python examples/{{name}}.py

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🧪 TESTING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Run all tests
test: test-python

# Run Python tests
test-python:
    @echo "Running Python tests..."
    @poetry run pytest tests/

# Run tests with coverage
test-cov:
    @echo "Running tests with coverage..."
    @poetry run pytest --cov=src/cogency tests/
    
# Run tests with verbose output
test-verbose:
    @echo "Running tests with verbose output..."
    @poetry run pytest -v tests/
    
# Run a specific test file or test
test-file file="":
    @echo "Running specific test: {{file}}..."
    @poetry run pytest -v tests/{{file}}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔍 CODE QUALITY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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

# Quick lint check (less strict, for development)
lint-dev:
    @echo "Running developer-friendly lint check..."
    @poetry run ruff check . --select="F,E9" --ignore="F401"

# Run all quality checks (format, lint, test)
check: format lint test
    @echo "All checks passed!"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 📚 DOCUMENTATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Generate API documentation
docs:
    @echo "Generating API documentation..."
    @cd website && poetry run python scripts/generate_docs.py

# Serve website documentation locally
website-serve:
    @echo "Starting website development server..."
    @cd website && npm run dev

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 📦 DISTRIBUTION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Build the Python package
build:
    @echo "Building Python package..."
    @poetry build

# Publish the Python package to PyPI
publish: check build
    @echo "Publishing Python package to PyPI..."
    @poetry publish

# Bump version (patch, minor, major)
bump level="patch":
    @echo "Bumping {{level}} version..."
    @poetry version {{level}}
    @echo "New version: $(poetry version -s)"

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🧹 MAINTENANCE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Clean build artifacts and cache directories
clean:
    @echo "Cleaning build artifacts and cache directories..."
    @rm -rf dist build .pytest_cache .mypy_cache .ruff_cache __pycache__ .venv .astro node_modules
    @find . -type d -name "__pycache__" -exec rm -rf {} +

# Show recent commits
commits:
    @git --no-pager log --pretty=format:"%ar %s"

# Run CI checks locally
ci: format lint test build
    @echo "CI checks completed successfully!"
    
# Fix test issues (format, lint, and run tests)
fix-tests: format fix test
    @echo "Tests fixed and verified!"