.PHONY: docs test coverage

build: docs test
	poetry build

publish: build
	poetry publish

docs:
	sphinx-build -b html "docs" "docs/_build/html"

test:
	nose2 --verbose

coverage:
	coverage run venv/bin/nose2 --verbose
	coverage report
	coverage html
