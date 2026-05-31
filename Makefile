.PHONY: install test run lint clean

install:
	pip install -e ".[dev]"

test:
	pytest -v

run:
	python app.py

lint:
	ruff check .
	ruff format --check .

format:
	ruff format .

clean:
	rm -rf __pycache__ .pytest_cache *.egg-info
