
.PHONY: static-check

pylint:
	echo Running pylint in zato-agent
	$(CURDIR)/../bin/pylint --verbose \
		--rcfile $(CURDIR)/../pylint.ini \
				 $(CURDIR)/../zato-agent/src/zato/agent

static-check:
	echo "Running static checks in zato-agent"
	$(CURDIR)/../bin/flake8 --version 1>&2
	$(CURDIR)/../bin/flake8 --config=$(CURDIR)/../tox.ini $(CURDIR)/

type-check:
	echo "Running type checks in zato-agent"
	pyright -p $(CURDIR)/../pyproject.toml .
