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


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🚀 DEVELOPMENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Run a specific example (hello, memory, research, coding)
example name="hello":
    @echo "Running example: {{name}}..."
    @poetry run python examples/{{name}}.py

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🧪 TESTING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Run all tests
test:
    @echo "Running all tests..."
    @poetry run pytest tests -v

# Run tests with coverage
test-cov:
    @poetry run pytest --cov=src/cogency tests/

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🧪 EVALUATIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Run fast eval suite (AGI lab validation - 6 evals, <30s)
eval-fast:
    @poetry run python -m evals.main fast

# Run fast eval suite (sequential for rate limits)
eval-fast-seq:
    @poetry run python -m evals.main fast --sequential

# Run fast eval suite (sequential + robust retry logic)
eval-fast-robust:
    @poetry run python -m evals.main fast --sequential --robust

# Run full eval suite (complete v1.0.0 - 15 evals)
eval-full:
    @poetry run python -m evals.main full

# Run full eval suite (sequential for rate limits)
eval-full-seq:
    @poetry run python -m evals.main full --sequential

# Run full eval suite (sequential + robust retry logic)
eval-full-robust:
    @poetry run python -m evals.main full --sequential --robust

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔍 CODE QUALITY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Format code
format:
    @poetry run ruff format .

# Lint code
lint:
    @poetry run ruff check .

# Fix linting issues
fix:
    @poetry run ruff check . --fix

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 📦 DISTRIBUTION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Build the Python package
build:
    @echo "Building Python package..."
    @poetry build

# Publish the Python package to PyPI
publish: ci build
    @echo "Publishing Python package to PyPI..."
    @poetry publish

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🧹 MAINTENANCE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Clean build artifacts and cache directories
clean:
    @echo "Cleaning build artifacts and cache directories..."
    @rm -rf dist build .pytest_cache .ruff_cache __pycache__ .venv .astro node_modules
    @find . -type d -name "__pycache__" -exec rm -rf {} +

# Show recent commits
commits:
    @git --no-pager log --pretty=format:"%ar %s"

# Run CI checks locally
ci: format fix test build