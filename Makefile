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
	COVERALLS_REPO_TOKEN=`cat coveralls_token` coveralls

view-docs: docs
	firefox docs/_build/html/index.html

docs: docs/_build/html/index.html

docs/_build/html/index.html: $(documentation) $(sources)
	sphinx-build -b $(docs_format) -D html_theme=$(docs_theme) "docs" "docs/_build/$(docs_format)"

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
	docker build -t dndice_compat . && docker run --rm --name rolling_test dndice_compat

clean:
	git clean -xdf -e '/venv' -e '/.idea' -e '/coveralls_token'
