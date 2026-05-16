default:
    @just --list

clean:
    @echo "Cleaning cogency..."
    @rm -rf dist build .pytest_cache .ruff_cache __pycache__ .venv
    @find . -type d -name "__pycache__" -exec rm -rf {} +

install:
    @uv sync

format:
    uv run ruff format . && uv run ruff check --fix . || true

lint:
    uv run ruff check . --ignore F841

typecheck:
    uv run pyright
    uv run pyright -p pyright.evals.json
    uv run pyright -p pyright.tests.json

test:
    @uv run pytest tests -q

ci: install lint typecheck test

example name="hello":
    @uv run python examples/{{name}}.py

cov:
    @uv run pytest --cov=src/cogency tests/

build:
    @uv build

publish: ci build
    @uv publish

commits:
    @git --no-pager log --pretty=format:"%h | %ar | %s"
