#options: sphinx_rtd_theme or one of the defaults (I like nature personally)
docs_theme ?= "sphinx_rtd_theme"

.PHONY: docs test coverage

build: docs test
	poetry build

publish: build
	poetry publish

docs:
	sphinx-build -b html -D html_theme=$(docs_theme) "docs" "docs/_build/html"
	firefox docs/_build/html/index.html

test:
	nose2 --verbose

coverage:
	coverage run venv/bin/nose2 --verbose
	coverage report
	coverage html
	firefox htmlcov/index.html
