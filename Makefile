SHELL = /bin/bash -o pipefail

.PHONY: help install install-poetry lock build check-wheel lint format lint-fix typecheck check-architecture \
	check-spec check-models generate-models test check-mutation test-e2e refresh-sample-profile refresh-golden check-quality check-all start-oxigraph stop-oxigraph oxigraph-load-test-data scan-files \
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
	@ poetry install --with test,lint,model

lock: ## Update poetry.lock
	@ poetry lock

build: ## Build the sdist and wheel into dist/ and check the wheel
	@ echo -e "$(BUILD_PRINT)Building the distribution$(END_BUILD_PRINT)"
	@ rm -rf dist
	@ poetry build
	@ $(MAKE) --no-print-directory check-wheel

check-wheel: ## Fail when the wheel lacks the report templates or the SPARQL queries
	@ unzip -l dist/*.whl | grep -q "$(TEMPLATES_PACKAGE)/fingerprint_report/templates/main.html" \
		|| (echo "wheel is missing the report templates" && exit 1)
	@ unzip -l dist/*.whl | grep -q "fingerprint/adapters/queries/q0_named_graphs.rq" \
		|| (echo "wheel is missing the SPARQL queries" && exit 1)

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

test: ## Unit, bdd and guard tests with coverage (no SPARQL store needed)
	@ echo -e "$(BUILD_PRINT)Running the unit tests$(END_BUILD_PRINT)"
	@ poetry run pytest $(TEST_PATH) --ignore=$(TEST_PATH)/e2e --hypothesis-profile=ci --cov=$(PACKAGE_NAME) --cov-branch --cov-report=term --cov-report=xml:coverage.xml --cov-fail-under=90 --junitxml=junit_report.xml
	@ echo -e "$(BUILD_PRINT)Checking 100% branch coverage of the domain layer$(END_BUILD_PRINT)"
	@ poetry run coverage report --include='fingerprint/domain/*' --omit='fingerprint/domain/profile.py,fingerprint/domain/views.py' --fail-under=100

check-mutation: ## Mutation score ratchet over domain and service_layer (slow, ~1 h; not part of check-all)
	@ echo -e "$(BUILD_PRINT)Running mutmut (about an hour)$(END_BUILD_PRINT)"
	@ poetry run mutmut run
	@ poetry run mutmut export-cicd-stats
	@ poetry run python $(TEST_PATH)/guards/mutation_score.py mutants/mutmut-cicd-stats.json $(TEST_PATH)/guards/mutation_score.txt \
		|| { status=$$?; [ $$status -ne 1 ] || poetry run mutmut results; exit $$status; }

test-e2e: ## End-to-end tests against the loaded test store (run oxigraph-load-test-data first); local only
	@ echo -e "$(BUILD_PRINT)Running the e2e tests against $${RDF_FINGERPRINTER_TEST_ENDPOINT:-$(OXIGRAPH)/query}$(END_BUILD_PRINT)"
	@ RDF_FINGERPRINTER_PREFIX_LOOKUP=false poetry run pytest $(TEST_PATH)/e2e

refresh-sample-profile: ## Regenerate tests/test_data/profiles/sample-profile.json from the store (run oxigraph-load-test-data first)
	@ echo -e "$(BUILD_PRINT)Refreshing the sample profile from $${RDF_FINGERPRINTER_TEST_ENDPOINT:-$(OXIGRAPH)/query}$(END_BUILD_PRINT)"
	@ RDF_FINGERPRINTER_PREFIX_LOOKUP=false poetry run python -m tests.refresh_sample_data

refresh-golden: ## Regenerate the golden outputs in tests/test_data/golden from the sample profile; writes only changed files
	@ echo -e "$(BUILD_PRINT)Refreshing the golden outputs$(END_BUILD_PRINT)"
	@ RDF_FINGERPRINTER_PREFIX_LOOKUP=false poetry run python -m tests.refresh_golden

#-----------------------------------------------------------------------------
# Profile model — LinkML sources in model/, generated read-only Pydantic (P-10)
#-----------------------------------------------------------------------------

MODEL_SRC = model/fingerprint_analytics.yaml
MODEL_OUT = $(PACKAGE_NAME)/domain/profile.py
MODEL_BANNER = \# GENERATED by make generate-models from model/*.yaml — DO NOT EDIT
GEN_PYDANTIC = poetry run gen-pydantic --extra-fields forbid --metadata --template-dir model/templates $(MODEL_SRC)
# The representation views (domain-object-model P-2, P-3): what the templates receive.
VIEWS_SRC = model/fingerprint_views.yaml
VIEWS_OUT = $(PACKAGE_NAME)/domain/views.py
GEN_VIEWS = poetry run gen-pydantic --extra-fields forbid --metadata --template-dir model/templates $(VIEWS_SRC)
# The published format of profile.json (profile-representations P-16): the raw run only.
SCHEMA_OUT = $(PACKAGE_NAME)/domain/profile_run.schema.json
GEN_SCHEMA = poetry run gen-json-schema --top-class ProfileRun model/fingerprint_stats.yaml

generate-models: ## Generate the Pydantic profile and views models and the profile.json schema from model/*.yaml
	@ echo -e "$(BUILD_PRINT)Generating $(MODEL_OUT), $(VIEWS_OUT) and $(SCHEMA_OUT)$(END_BUILD_PRINT)"
	@ { echo "$(MODEL_BANNER)"; $(GEN_PYDANTIC); } > $(MODEL_OUT)
	@ { echo "$(MODEL_BANNER)"; $(GEN_VIEWS); } > $(VIEWS_OUT)
	@ $(GEN_SCHEMA) > $(SCHEMA_OUT)

check-models: ## Fail when the generated model or schema is out of date with model/*.yaml
	@ echo -e "$(BUILD_PRINT)Checking the generated model is in sync$(END_BUILD_PRINT)"
	@ { echo "$(MODEL_BANNER)"; $(GEN_PYDANTIC); } | diff -q $(MODEL_OUT) - >/dev/null \
		|| (echo "$(MODEL_OUT) is out of date: run make generate-models" && exit 1)
	@ { echo "$(MODEL_BANNER)"; $(GEN_VIEWS); } | diff -q $(VIEWS_OUT) - >/dev/null \
		|| (echo "$(VIEWS_OUT) is out of date: run make generate-models" && exit 1)
	@ $(GEN_SCHEMA) | diff -q $(SCHEMA_OUT) - >/dev/null \
		|| (echo "$(SCHEMA_OUT) is out of date: run make generate-models" && exit 1)

check-quality: lint typecheck check-architecture check-models check-spec ## Static checks
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

SCAN_STORE = http://localhost:$(RDF_FINGERPRINTER_SCAN_PORT)
SCAN_SCHEMA = urn:fingerprint:scan:schema
SCAN_DATA = urn:fingerprint:scan:data
rdf_type = $(if $(filter %.ttl,$(1)),text/turtle,application/rdf+xml)

scan-files: ## Fingerprint files with the pitfall scan: make scan-files ONTOLOGY=o.owl [DATA=d.rdf] OUT=dir (own store)
	@ test -n "$(ONTOLOGY)" -a -n "$(OUT)" || { echo "usage: make scan-files ONTOLOGY=<file> [DATA=<file>] OUT=<folder>"; exit 2; }
	@ echo -e "$(BUILD_PRINT)Scanning $(ONTOLOGY) $(DATA) on the scan store, port $(RDF_FINGERPRINTER_SCAN_PORT)$(END_BUILD_PRINT)"
	@ $(COMPOSE) up -d oxigraph-scan
	@ for i in $$(seq 30); do curl -sf -o /dev/null $(SCAN_STORE)/ && break; sleep 1; done
	@ curl -sf -X DELETE "$(SCAN_STORE)/store?graph=$(SCAN_SCHEMA)" -o /dev/null || true
	@ curl -sf -X DELETE "$(SCAN_STORE)/store?graph=$(SCAN_DATA)" -o /dev/null || true
	@ curl -sf -X POST -H content-type:$(call rdf_type,$(ONTOLOGY)) --data-binary @$(ONTOLOGY) "$(SCAN_STORE)/store?graph=$(SCAN_SCHEMA)"
	@ $(if $(DATA),curl -sf -X POST -H content-type:$(call rdf_type,$(DATA)) --data-binary @$(DATA) "$(SCAN_STORE)/store?graph=$(SCAN_DATA)",true)
	@ mkdir -p $(OUT)
	@ poetry run fingerprint -e $(SCAN_STORE)/query -o $(OUT) $(if $(DATA),--graph $(SCAN_DATA)) --graph $(SCAN_SCHEMA) \
		--pitfalls --schema-graph $(SCAN_SCHEMA) --format pitfalls $(SCAN_ARGS); status=$$?; \
		echo "fingerprint exit status: $$status (1 = failures recorded, 5 = pitfalls at --fail-on)"; exit $$status

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
