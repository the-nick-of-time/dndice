#options: sphinx_rtd_theme or one of the defaults (I like nature personally)
docs_theme ?= "sphinx_rtd_theme"
docs_format ?= html

.PHONY: docs test coverage clean

SOURCES=$(wildcard dndice/*.py) $(wildcard dndice/lib/*.py)


build: docs test
	poetry build

publish: build
	poetry publish

docs:
	sphinx-build -b $(docs_format) -D html_theme=$(docs_theme) "docs" "docs/_build/$(docs_format)"
	firefox docs/_build/html/index.html

test:
	nose2 --verbose

coverage:
	coverage run venv/bin/nose2 --verbose
	coverage report
	coverage html
	firefox htmlcov/index.html

compatibility:
	docker build -t dndice_compat . && docker run --rm --name rolling_test dndice_compat

clean:
	rm -rf docs/_build/
	rm -rf dist/
	rm -rf htmlcov/
	rm -f .coverage
