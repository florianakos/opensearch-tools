PYTHON ?= python3.11
VENV   ?= venv
SRC    := shovel

export PATH := $(VENV)/bin:$(PATH)

it: integration-tests
integration-tests:
	AWS_DEFAULT_REGION=eu-west-1 OPENSEARCH_DOMAIN_NAME=test_os_domain docker compose up --force-recreate --build --abort-on-container-exit --exit-code-from integration_tests

$(VENV)/.stamp:
	$(PYTHON) -m venv '$(VENV)'
	. $(VENV)/bin/activate; python -m pip install --upgrade pip setuptools wheel pip-tools
	touch $@

$(VENV)/.dev.stamp: $(VENV)/.stamp shovel/requirements.txt shovel/requirements-dev.txt
	cd shovel && \
		pip-sync requirements.txt requirements-dev.txt
	touch $@

.PHONY: lint
lint: $(VENV)/.dev.stamp
	black --check $(SRC)
	isort --check $(SRC)
	pylint $(SRC)
	mypy $(SRC)

.PHONY: update-shovel-deps
update-shovel-deps: $(VENV)/.stamp
	cd shovel && \
		pip-compile --allow-unsafe --generate-hashes -U requirements.in && \
		pip-compile --allow-unsafe --generate-hashes -U requirements-dev.in

.PHONY: install-shovel-deps
install-shovel-deps: $(VENV)/.stamp install-shovel-dev-deps
	. $(VENV)/bin/activate; pip install -r shovel/requirements.txt

.PHONY: install-shovel-dev-deps
install-shovel-dev-deps: $(VENV)/.dev.stamp
	. $(VENV)/bin/activate; pip install -r shovel/requirements-dev.txt
