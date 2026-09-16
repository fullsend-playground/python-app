.PHONY: install test run lint clean format

install:
	uv sync

test:
	uv run pytest -v

run:
	uv run python app.py

lint:
	uv run ruff check .
	uv run ruff format --check .

format:
	uv run ruff format .

clean:
	rm -rf __pycache__ .pytest_cache *.egg-info .venv
