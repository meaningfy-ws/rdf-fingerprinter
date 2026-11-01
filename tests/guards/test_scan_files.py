"""`make scan-files` loads files into its own store and scans them (developer-tooling › Scan files locally).

It needs Docker, so these guards read the Makefile and the compose file instead of running the target.
"""

from pathlib import Path

import yaml

from tests.guards.makefile import recipe

DOCKER = Path(__file__).parents[2] / "docker"


def env() -> dict[str, str]:  # dict-ok: docker/.env being parsed
    lines = (DOCKER / ".env").read_text().splitlines()
    return dict(line.split("=", 1) for line in lines if "=" in line)  # dict-ok: docker/.env being parsed


def test_scan_files_loads_the_ontology_and_the_data_and_runs_the_scan():
    _, text = recipe("scan-files")
    assert "$(SCAN_STORE)/store?graph=$(SCAN_SCHEMA)" in text and "$(SCAN_STORE)/store?graph=$(SCAN_DATA)" in text
    assert "--pitfalls --schema-graph $(SCAN_SCHEMA) --format pitfalls" in text
    assert "--graph $(SCAN_DATA)" in text and "--graph $(SCAN_SCHEMA)" in text


def test_scan_files_never_touches_the_e2e_store():
    _, text = recipe("scan-files")
    assert "$(OXIGRAPH)" not in text and "up -d oxigraph-scan" in text
    services = yaml.safe_load((DOCKER / "docker-compose.yml").read_text())["services"]
    assert services["oxigraph-scan"]["container_name"] != services["oxigraph"]["container_name"]
    assert env()["RDF_FINGERPRINTER_SCAN_PORT"] != env()["RDF_FINGERPRINTER_OXIGRAPH_PORT"]
