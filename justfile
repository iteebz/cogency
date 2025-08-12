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

# Run capability evaluation suite (current cogency features)
eval-capability:
    @poetry run python -m evals.runner capability

# Run memory benchmark suite (competitive differentiator)
eval-memory:
    @poetry run python -m evals.runner memory

# Run security evaluation (injection resistance)
eval-security:
    @poetry run python -m evals.runner security

# Run tool integration evaluation
eval-tools:
    @poetry run python -m evals.runner tools

# Run individual memory benchmarks
eval-cross-session:
    @poetry run python -m evals.runner cross_session

eval-temporal:
    @poetry run python -m evals.runner temporal

eval-interference:
    @poetry run python -m evals.runner interference

# Run profile manager memory test (current system)
eval-profile-memory:
    @poetry run python -m evals.runner profile_memory

# Run all evaluation benchmarks (comprehensive suite)
eval-all:
    @poetry run python -m evals.runner all

# Run all evaluations (alias for eval-all)
eval: eval-all

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
    @poetry run ruff check . --fix --unsafe-fixes

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