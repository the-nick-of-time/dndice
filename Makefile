SOURCES=$(wildcard dndice/*.py) $(wildcard dndice/lib/*.py)


build: docs test
	poetry build

publish: build
	poetry publish

docs: $(SOURCES)
	sphinx-build -b html "docs" "docs/_build/html"

test:
	nose2 --verbose

coverage:
	coverage run venv/bin/nose2 --verbose
	coverage report
	coverage html

compatibility:
	docker build -t dndice_compat . && docker run --rm --name rolling_test dndice_compat
