default:
    @just --list

clean:
    @echo "Cleaning cogency..."
    @rm -rf dist build .pytest_cache .ruff_cache __pycache__ .venv
    @find . -type d -name "__pycache__" -exec rm -rf {} +

install:
    @poetry lock
    @poetry install

ci:
    @poetry run ruff format .
    @poetry run ruff check . --fix --unsafe-fixes
    @poetry run pyright
    @poetry run pytest tests -q
    @poetry build

example name="hello":
    @poetry run python examples/{{name}}.py

test:
    @poetry run pytest tests

cov:
    @poetry run pytest --cov=src/cogency tests/

format:
    @poetry run ruff format .

lint:
    @poetry run ruff check . --ignore F841

fix:
    @poetry run ruff check . --fix --unsafe-fixes

build:
    @poetry build

publish: ci build
    @poetry publish

commits:
    @git --no-pager log --pretty=format:"%h | %ar | %s"
