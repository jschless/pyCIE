.PHONY: bootstrap check labs run-lab01 run-foundations docs-install docs-serve docs-build

bootstrap:
	python -m venv .venv
	. .venv/bin/activate && pip install -e '.[dev]'

check:
	pytest -q

labs:
	PYTHONPATH=src python -m pycie labs

run-lab01:
	PYTHONPATH=src python -m pycie run lab01

run-foundations:
	PYTHONPATH=src python -m pycie run lab06a
	PYTHONPATH=src python -m pycie run lab06b
	PYTHONPATH=src python -m pycie run lab06c

docs-install:
	. .venv/bin/activate && pip install -e '.[docs]'

docs-serve:
	. .venv/bin/activate && mkdocs serve

docs-build:
	. .venv/bin/activate && mkdocs build --strict
