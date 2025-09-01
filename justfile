default:
    @just --list

install:
    @poetry install

example name="hello":
    @poetry run python examples/{{name}}.py

test:
    @poetry run python -m pytest tests -v

cov:
    @poetry run pytest --cov=src/cogency tests/


format:
    @poetry run ruff format .

lint:
    @poetry run ruff check .

fix:
    @poetry run ruff check . --fix --unsafe-fixes

build:
    @poetry build

publish: ci build
    @poetry publish

clean:
    @rm -rf dist build .pytest_cache .ruff_cache __pycache__ .venv
    @find . -type d -name "__pycache__" -exec rm -rf {} +

commits:
    @git --no-pager log --pretty=format:"%ar %s"

ci: format fix test build