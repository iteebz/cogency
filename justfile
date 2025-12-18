default:
    @just --list

clean:
    @echo "Cleaning cogency..."
    @rm -rf dist build .pytest_cache .ruff_cache __pycache__ .venv
    @find . -type d -name "__pycache__" -exec rm -rf {} +

install:
    @uv sync

ci:
    @uv run ruff format .
    @uv run ruff check . --fix --unsafe-fixes
    @uv run ruff check .
    @uv run pyright
    @uv run pyright -p pyright.evals.json
    @uv run pyright -p pyright.tests.json
    @uv run pytest tests -q
    @uv build

example name="hello":
    @uv run python examples/{{name}}.py

test:
    @uv run pytest tests

cov:
    @uv run pytest --cov=src/cogency tests/

format:
    @uv run ruff format .

lint:
    @uv run ruff check . --ignore F841

fix:
    @uv run ruff check . --fix --unsafe-fixes

build:
    @uv build

publish: ci build
    @uv publish

commits:
    @git --no-pager log --pretty=format:"%h | %ar | %s"
