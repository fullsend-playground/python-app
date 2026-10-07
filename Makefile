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

.PHONY: test-pi-script-loop
test-pi-script-loop:
	PI_BIN="$${PI_BIN:-$$(pwd)/examples/pi-script-loop/node_modules/.bin/pi}" node examples/pi-script-loop/prove-startup.mjs
