#options: sphinx_rtd_theme or one of the defaults (I like nature personally)
docs_theme ?= "sphinx_rtd_theme"
docs_format ?= html

sources = $(wildcard dndice/lib/*.py) $(wildcard dndice/*.py)
tests = $(wildcard tests/*.py)
documentation = $(wildcard docs/*.rst) docs/conf.py

.PHONY: docs view-docs test coverage view-coverage clean build publish


build: coverage docs
	poetry build

publish: build
	poetry publish

view-docs: docs
	firefox docs/_build/html/index.html

docs: docs-$(docs_format)

docs-html: docs/_build/html/index.html
docs/_build/html/index.html: $(documentation) $(sources)
	sphinx-build -b html -D html_theme=$(docs_theme) "docs" "docs/_build/html"

docs-man: docs/_build/man/dndice.1
docs/_build/man/dndice.1: $(documentation) $(sources)
	sphinx-build -b man "docs" "docs/_build/man"

docs-epub: docs/_build/epub/dndice.epub
docs/_build/epub/dndice.epub: $(documentation) $(sources)
	sphinx-build -b epub "docs" "docs/_build/epub"

# Intentionally have no prerequisites; should be able to run tests even if nothing has changed
test:
	nose2 --verbose

view-coverage: coverage
	firefox htmlcov/index.html

coverage: htmlcov/index.html

.coverage: $(sources) $(tests) .coveragerc
	coverage run -m nose2 --verbose
	coverage report

htmlcov/index.html: .coverage
	coverage html

compatibility: Dockerfile $(sources) $(tests)
	for v in "python:3.5-alpine" "python:3.8-alpine" "jamiehewland/alpine-pypy:3.6-alpine3.11" ; do \
	docker build -t dndice_compat --build-arg image="$$v" . && docker run --rm --name rolling_test dndice_compat ; \
	done

clean:
	git clean -xdf -e '/venv' -e '/.idea'
