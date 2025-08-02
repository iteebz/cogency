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
test:
    @echo "Running all tests..."
    @poetry run pytest tests -v

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

# Run tests in parallel (fast unit tests)
test-parallel:
    @echo "Running unit tests in parallel..."
    @poetry run pytest tests/unit -n auto -m "not slow"

# Run integration tests (sequential, as they may need isolation)
test-integration:
    @echo "Running integration tests..."
    @poetry run pytest tests/integration -v

# Run contract validation tests
test-contracts:
    @echo "Running API contract tests..."
    @poetry run pytest tests -k "contract" -v

# Run schema validation tests  
test-schema:
    @echo "Running schema validation tests..."
    @poetry run pytest tests -k "schema" -v

# Fast test suite (parallel units + essential integration)
test-fast:
    @echo "Running fast test suite..."
    @poetry run pytest tests/unit -n auto -m "not slow" && poetry run pytest tests/integration/test_api_contracts.py -v

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🧪 EVALUATIONS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Run quick evals (basic functionality)
eval-quick:
    @echo "Running quick eval suite..."
    @cd evals && poetry run python run_suite.py quick

# Run full eval suite
eval-full:
    @echo "Running full eval suite..."
    @cd evals && poetry run python run_suite.py full

# Run provider comparison (requires multiple API keys)
eval-providers:
    @echo "Running provider eval suite..."
    @cd evals && poetry run python run_suite.py provider

# Run eval suite (quick by default)
eval suite="quick":
    @echo "Running {{suite}} eval suite..."
    @cd evals && poetry run python run_suite.py {{suite}}

# Run benchmarked eval suite
eval-bench suite="quick":
    @echo "Benchmarking {{suite}} eval suite..."
    @cd evals && poetry run python run_suite_bench.py {{suite}}

# Run cross-provider benchmarking
eval-cross suite="quick":
    @echo "Cross-provider benchmarking {{suite}} eval suite..."
    @cd evals && poetry run python run_cross_provider.py {{suite}}

# Run all evaluations
eval-all:
    @echo "Running all evaluations..."
    @cd evals && poetry run python run_suite.py full

# Run SWE benchmark
eval-swe:
    @echo "Running SWE benchmark..."
    @poetry run python -m evals.benchmarks.swe

# List available evaluations
eval-list:
    @echo "Available evaluations:"
    @poetry run python -m cogency.evals list

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔍 CODE QUALITY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Format code with ruff
format:
    @echo "Formatting Python code with black..."
    @poetry run black .

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
    @rm -rf dist build .pytest_cache .ruff_cache __pycache__ .venv .astro node_modules
    @find . -type d -name "__pycache__" -exec rm -rf {} +

# Show recent commits
commits:
    @git --no-pager log --pretty=format:"%ar %s"

# Run CI checks locally
ci: format fix
	@echo "Running tests for CI..."
	@poetry run pytest tests/
	@just build
	@echo "CI checks completed successfully!"
    
# Fix test issues (format, lint, and run tests)
fix-tests: format fix test
    @echo "Tests fixed and verified!"