"""The Makefile and the workflows wire the gates the developer-tooling spec relies on.

These check the wiring only; that GitHub runs a workflow, or PyPI accepts an upload, is not tested here.
"""

import re
from pathlib import Path

import yaml

from tests.guards.makefile import MAKEFILE
from tests.guards.makefile import recipe as _recipe

ROOT = Path(__file__).parents[2]
GATES = ("lint", "typecheck", "check-architecture", "check-models", "check-spec")


def _workflow(name: str) -> dict:  # dict-ok: parsed YAML
    return yaml.safe_load((ROOT / ".github" / "workflows" / f"{name}.yml").read_text())


def _triggers(workflow: dict) -> dict:  # dict-ok: parsed YAML
    return workflow.get("on") or workflow[True]  # YAML reads a bare `on` as True


def _steps(workflow: dict) -> list[dict]:  # dict-ok: parsed YAML
    return [step for job in workflow["jobs"].values() for step in job["steps"]]


def test_check_all_runs_every_static_check_and_the_tests():
    check_all, _ = _recipe("check-all")
    check_quality, _ = _recipe("check-quality")
    assert check_all == ["check-quality", "test"]
    assert set(GATES) <= set(check_quality)


def test_the_gate_runs_the_properties_in_parallel_with_the_floors():
    _, test = _recipe("test")
    for flag in ("-n auto", "--hypothesis-profile=ci", '-m "not release"', "--ignore=tests/e2e", "--cov-fail-under=90"):
        assert flag in test, flag
    assert re.search(r"coverage report .*--fail-under=100", test)


def test_check_release_runs_the_release_tests_the_random_properties_and_e2e():
    check_release, _ = _recipe("check-release")
    _, release = _recipe("test-release")
    _, properties = _recipe("test-properties")
    assert check_release == ["check-all", "test-release", "test-properties", "test-e2e"]
    assert "-m release" in release
    assert "-m hypothesis" in properties and "--hypothesis-profile=dev" in properties


def test_the_test_target_runs_pytest_with_a_coverage_floor_and_no_recipe_line_ignores_failure():
    _, recipe = _recipe("test")
    assert "poetry run pytest" in recipe
    assert re.search(r"--cov-fail-under=\d+", recipe)
    assert not [line for line in recipe.splitlines() if line.lstrip().startswith("-") or "|| true" in line]


def test_ci_runs_check_all_on_push_and_pull_request_to_master_and_develop():
    workflow = _workflow("ci")
    triggers = _triggers(workflow)
    assert triggers["push"]["branches"] == ["master", "develop"]
    assert triggers["pull_request"]["branches"] == ["master", "develop"]
    assert any(step.get("run") == "make check-all" for step in _steps(workflow))
    upload = next(step for step in _steps(workflow) if "codecov-action" in step.get("uses", ""))
    assert upload["with"]["files"] == "coverage.xml"


def test_the_release_check_runs_e2e_on_a_store_and_installs_the_wheel():
    workflow = _workflow("release-check")
    triggers = _triggers(workflow)
    assert triggers["pull_request"]["branches"] == ["master"] and "workflow_dispatch" in triggers
    assert any("oxigraph" in service for job in workflow["jobs"].values() for service in job.get("services", {}))
    runs = [step.get("run", "") for step in _steps(workflow)]
    commands = ("make load-test-data", "make test-release", "make test-e2e", "pip install dist/*.whl", "fingerprint --help")
    for command in commands:
        assert any(command in run for run in runs), command


def test_mutation_runs_after_a_release_and_on_demand():
    workflow = _workflow("mutation")
    triggers = _triggers(workflow)
    assert triggers["release"]["types"] == ["published"] and "workflow_dispatch" in triggers
    assert "schedule" not in triggers
    assert any(step.get("run") == "make check-mutation" for step in _steps(workflow))


def test_the_release_workflow_publishes_through_oidc_without_a_token():
    workflow = _workflow("publish")
    assert _triggers(workflow)["release"]["types"] == ["published"]
    pypi = workflow["jobs"]["pypi"]
    assert pypi["permissions"]["id-token"] == "write"
    publish = next(step for step in pypi["steps"] if "pypi-publish" in step.get("uses", ""))
    assert not {"password", "user"} & set(publish.get("with", {}))
    assert "secrets." not in (ROOT / ".github" / "workflows" / "publish.yml").read_text().replace("# ", "")


def test_the_release_workflow_builds_with_poetry_and_checks_the_wheel():
    build = " ".join(step.get("run", "") for step in _workflow("publish")["jobs"]["build"]["steps"])
    assert "make build" in build
    build_recipe, build_prereqs = _recipe("build")[1], _recipe("build")[0]
    assert "poetry build" in build_recipe
    assert "check-wheel" in build_recipe + " ".join(build_prereqs)
    assert "$(TEMPLATES_PACKAGE)" in _recipe("check-wheel")[1]
    assert "fingerprint/adapters/queries/" in _recipe("check-wheel")[1]
    assert "TEMPLATES_PACKAGE = fingerprint_report_templates" in MAKEFILE.read_text()


def test_the_docs_workflow_builds_with_antora_on_pull_requests():
    workflow = _workflow("docs")
    assert "pull_request" in _triggers(workflow)
    assert any(step.get("run") == "make build-docs" for step in workflow["jobs"]["build"]["steps"])
    assert "antora" in _recipe("build-docs")[1]


def test_the_docs_workflow_deploys_only_after_the_build_and_only_from_master():
    deploy = _workflow("docs")["jobs"]["deploy"]
    assert deploy["needs"] == "build"
    assert "refs/heads/master" in deploy["if"] and "pull_request" in deploy["if"]


def test_check_models_regenerates_and_diffs_every_generated_module_inside_the_gate():
    _, recipe = _recipe("check-models")
    for output in ("$(MODEL_OUT)", "$(VIEWS_OUT)", "$(SCHEMA_OUT)"):
        assert re.search(rf"diff -q {re.escape(output)} -", recipe), output
    assert "check-models" in _recipe("check-quality")[0]
