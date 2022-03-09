#options: sphinx_rtd_theme or one of the defaults (I like nature personally)
docs_theme ?= "sphinx_rtd_theme"
docs_format ?= html

sources = $(wildcard dndice/lib/*.py) $(wildcard dndice/*.py)
tests = $(wildcard tests/*.py)
documentation = $(wildcard docs/*.rst) docs/conf.py

version := $(shell poetry version --short)

dist/dndice-$(version).tar.gz dist/dndice-$(version)-py3-none-any.whl: .coverage docs/_build/html/index.html
	poetry build

docs/_build/html/index.html: $(documentation) $(sources)
	sphinx-build -b $(docs_format) -D html_theme=$(docs_theme) "docs" "docs/_build/$(docs_format)"

.coverage: $(sources) $(tests) .coveragerc
	coverage run -m nose2 --verbose
	coverage report

htmlcov/index.html: .coverage
	coverage html
