"""The Makefile and the workflows wire the gates the developer-tooling spec relies on.

These check the wiring only; that GitHub runs a workflow, or PyPI accepts an upload, is not tested here.
"""

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).parents[2]
GATES = ("lint", "typecheck", "check-architecture", "check-models", "check-spec")


def _makefile() -> str:
    return (ROOT / "Makefile").read_text()


def _recipe(target: str) -> tuple[list[str], str]:
    """The prerequisites and the recipe text of a Makefile target."""
    match = re.search(rf"^{re.escape(target)}:([^\n#]*)(?:##[^\n]*)?\n((?:\t[^\n]*\n)*)", _makefile(), re.MULTILINE)
    assert match, f"Makefile has no target {target}"
    return match.group(1).split(), match.group(2)


def _workflow(name: str) -> dict:  # dict-ok: parsed YAML
    return yaml.safe_load((ROOT / ".github" / "workflows" / f"{name}.yml").read_text())


def _triggers(workflow: dict) -> dict:  # dict-ok: parsed YAML
    return workflow.get("on") or workflow[True]  # YAML reads a bare `on` as True


def _steps(workflow: dict) -> list[dict]:  # dict-ok: parsed YAML
    return [step for job in workflow["jobs"].values() for step in job["steps"]]


def test_check_all_runs_every_static_check_and_the_tests():
    check_all, _ = _recipe("check-all")
    check_quality, _ = _recipe("check-quality")
    assert "test" in check_all and "check-quality" in check_all
    assert set(GATES) <= set(check_quality)


def test_the_test_target_runs_pytest_and_fails_on_a_failing_test():
    _, recipe = _recipe("test")
    assert "poetry run pytest" in recipe


def test_ci_runs_check_all_on_push_and_pull_request_to_master():
    workflow = _workflow("ci")
    triggers = _triggers(workflow)
    assert triggers["push"]["branches"] == ["master"]
    assert triggers["pull_request"]["branches"] == ["master"]
    assert any(step.get("run") == "make check-all" for step in _steps(workflow))


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
    assert "TEMPLATES_PACKAGE = fingerprint_report_templates" in _makefile()


def test_the_docs_workflow_builds_on_pull_requests_and_deploys_only_from_master():
    workflow = _workflow("docs")
    assert "pull_request" in _triggers(workflow)
    assert any(step.get("run") == "make build-docs" for step in workflow["jobs"]["build"]["steps"])
    assert "antora" in _recipe("build-docs")[1]
    deploy = workflow["jobs"]["deploy"]
    assert deploy["needs"] == "build"
    assert "refs/heads/master" in deploy["if"] and "pull_request" in deploy["if"]


def test_check_models_regenerates_and_diffs_every_generated_module_inside_the_gate():
    _, recipe = _recipe("check-models")
    for output in ("$(MODEL_OUT)", "$(VIEWS_OUT)", "$(SCHEMA_OUT)"):
        assert re.search(rf"diff -q {re.escape(output)} -", recipe), output
    assert "check-models" in _recipe("check-quality")[0]
