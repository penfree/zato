
.PHONY: static-check

PY_DIR=$(CURDIR)/../bin

run-tests:
	echo "Running unit-tests in zato-distlock"
	$(PY_DIR)/nosetests $(CURDIR)/test/zato/distlock/test_*.py -s

pylint:
	echo Running pylint in zato-distlock
	$(CURDIR)/../bin/pylint --verbose \
		--rcfile $(CURDIR)/../pylint.ini \
				 $(CURDIR)/../zato-distlock/src/zato/distlock

static-check:
	echo "Running static checks in zato-distlock"
	$(CURDIR)/../bin/flake8 --config=$(CURDIR)/../tox.ini $(CURDIR)/
