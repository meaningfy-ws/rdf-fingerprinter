SHELL = /bin/bash -o pipefail

.PHONY: help install install-poetry lock build check-wheel lint format lint-fix typecheck check-architecture \
	check-spec test test-e2e check-quality check-all start-oxigraph stop-oxigraph oxigraph-load-test-data \
	install-antora build-docs clean-docs serve-docs preview-docs

include docker/.env

BUILD_PRINT = \e[1;34mSTEP: \e[0m
END_BUILD_PRINT = \e[0m

PACKAGE_NAME = fingerprint
TEMPLATES_PACKAGE = fingerprint_report_templates
TEST_PATH = tests
OPENSPEC = npx -y @fission-ai/openspec@1.4.1
COMPOSE = docker compose --file docker/docker-compose.yml --env-file docker/.env
TEST_DATA = tests/test_data
GRAPH_BASE = http://publications.europa.eu/resources/authority
OXIGRAPH = http://localhost:$(RDF_FINGERPRINTER_OXIGRAPH_PORT)
# Coverage is reported, not gated.
COV_FLAGS = --cov=$(PACKAGE_NAME) --cov-report=term --cov-report=xml:coverage.xml

.DEFAULT_GOAL := help

help: ## Display available targets
	@ grep -hE '^[a-zA-Z0-9_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-26s\033[0m %s\n", $$1, $$2}'

#-----------------------------------------------------------------------------
# Install / build
#-----------------------------------------------------------------------------

install-poetry: ## Install Poetry if not present
	@ command -v poetry >/dev/null || python -m pip install "poetry>=2.0.0,<3.0.0"

install: install-poetry ## Install the package with all dependency groups
	@ echo -e "$(BUILD_PRINT)Installing dependencies$(END_BUILD_PRINT)"
	@ poetry install --with test,lint

lock: ## Update poetry.lock
	@ poetry lock

build: ## Build the sdist and wheel into dist/ and check the wheel
	@ echo -e "$(BUILD_PRINT)Building the distribution$(END_BUILD_PRINT)"
	@ rm -rf dist
	@ poetry build
	@ $(MAKE) --no-print-directory check-wheel

check-wheel: ## Fail when the wheel lacks the report templates
	@ unzip -l dist/*.whl | grep -q "$(TEMPLATES_PACKAGE)/fingerprint_report/templates/main.html" \
		|| (echo "wheel is missing the report templates" && exit 1)

#-----------------------------------------------------------------------------
# Quality gates — `make check-all` is the gate CI runs
#-----------------------------------------------------------------------------

lint: ## Ruff lint and format check
	@ echo -e "$(BUILD_PRINT)Ruff$(END_BUILD_PRINT)"
	@ poetry run ruff check $(PACKAGE_NAME) $(TEMPLATES_PACKAGE) $(TEST_PATH)
	@ poetry run ruff format --check $(PACKAGE_NAME) $(TEMPLATES_PACKAGE) $(TEST_PATH)

format: ## Format code with Ruff
	@ poetry run ruff format $(PACKAGE_NAME) $(TEMPLATES_PACKAGE) $(TEST_PATH)

lint-fix: ## Ruff auto-fix
	@ poetry run ruff check --fix $(PACKAGE_NAME) $(TEMPLATES_PACKAGE) $(TEST_PATH)

typecheck: ## mypy type check of the package
	@ echo -e "$(BUILD_PRINT)mypy$(END_BUILD_PRINT)"
	@ poetry run mypy $(PACKAGE_NAME)

check-architecture: ## Check layer boundaries (import-linter)
	@ echo -e "$(BUILD_PRINT)Checking layer boundaries (import-linter)$(END_BUILD_PRINT)"
	@ poetry run lint-imports --config .importlinter

check-spec: ## Validate the OpenSpec spine strictly (needs Node.js)
	@ echo -e "$(BUILD_PRINT)openspec validate --strict$(END_BUILD_PRINT)"
	@ $(OPENSPEC) validate --all --strict

test: ## Unit tests with coverage (no SPARQL store needed)
	@ echo -e "$(BUILD_PRINT)Running the unit tests$(END_BUILD_PRINT)"
	@ poetry run pytest $(TEST_PATH)/unit $(COV_FLAGS) --junitxml=junit_report.xml

test-e2e: ## End-to-end tests against the loaded test store (run oxigraph-load-test-data first); local only
	@ echo -e "$(BUILD_PRINT)Running the e2e tests against $${RDF_FINGERPRINTER_TEST_ENDPOINT:-$(OXIGRAPH)/query}$(END_BUILD_PRINT)"
	@ poetry run pytest $(TEST_PATH)/e2e

check-quality: lint typecheck check-architecture check-spec ## Static checks
	@ echo -e "$(BUILD_PRINT)All quality checks passed$(END_BUILD_PRINT)"

check-all: check-quality test ## The full gate: static checks + tests
	@ echo -e "$(BUILD_PRINT)Full verification suite passed$(END_BUILD_PRINT)"

#-----------------------------------------------------------------------------
# Test SPARQL store — Oxigraph only (DEC-10)
#-----------------------------------------------------------------------------

start-oxigraph: ## Start an in-memory Oxigraph on RDF_FINGERPRINTER_OXIGRAPH_PORT
	@ echo -e "$(BUILD_PRINT)Starting Oxigraph on port $(RDF_FINGERPRINTER_OXIGRAPH_PORT)$(END_BUILD_PRINT)"
	@ $(COMPOSE) up -d oxigraph
	@ for i in $$(seq 30); do curl -sf -o /dev/null $(OXIGRAPH)/ && exit 0; sleep 1; done; echo "Oxigraph did not start" && exit 1

stop-oxigraph: ## Stop Oxigraph
	@ $(COMPOSE) rm -sf oxigraph

oxigraph-load-test-data: start-oxigraph ## Load the test graphs into Oxigraph (endpoint $(OXIGRAPH)/query)
	@ echo -e "$(BUILD_PRINT)Loading the test data into Oxigraph$(END_BUILD_PRINT)"
	@ curl -sf -X DELETE "$(OXIGRAPH)/store?graph=$(GRAPH_BASE)/continents" -o /dev/null || true
	@ curl -sf -X DELETE "$(OXIGRAPH)/store?graph=$(GRAPH_BASE)/treaties" -o /dev/null || true
	@ curl -sf -X DELETE "$(OXIGRAPH)/store?default" -o /dev/null || true
	@ curl -sf -X POST -H content-type:application/rdf+xml --data-binary @$(TEST_DATA)/continents-source-ap.rdf "$(OXIGRAPH)/store?graph=$(GRAPH_BASE)/continents"
	@ curl -sf -X POST -H content-type:application/rdf+xml --data-binary @$(TEST_DATA)/treaties-source-ap.rdf "$(OXIGRAPH)/store?graph=$(GRAPH_BASE)/treaties"
	@ curl -sf -X POST -H content-type:application/rdf+xml --data-binary @$(TEST_DATA)/continents-source-ap.rdf "$(OXIGRAPH)/store?default"

#-----------------------------------------------------------------------------
# Documentation (AsciiDoc + Antora, Node-based) — published to GitHub Pages (DEC-6)
#-----------------------------------------------------------------------------

DOC_BUILD_DIR = docs/build
ANTORA_PLAYBOOK = docs/antora-playbook.yml

install-antora: ## Install Antora (npm; needs Node.js)
	@ echo -e "$(BUILD_PRINT)Installing Antora (npm)$(END_BUILD_PRINT)"
	@ npm install

build-docs: install-antora ## Build the documentation site into docs/build/site
	@ echo -e "$(BUILD_PRINT)Building the documentation site with Antora$(END_BUILD_PRINT)"
	@ npx antora --fetch $(ANTORA_PLAYBOOK)

clean-docs: ## Remove the documentation build
	@ rm -rf $(DOC_BUILD_DIR)

serve-docs: ## Serve the built docs at http://localhost:8088
	@ python3 -m http.server 8088 --directory $(DOC_BUILD_DIR)/site

preview-docs: build-docs serve-docs ## Build and serve the docs
