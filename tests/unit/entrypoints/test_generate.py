"""The generator commands (UC-B2.1): parse, call the representations service, exit 0/2/4 (P-3, P-4, P-13)."""

import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from fingerprint.entrypoints.cli import generate
from tests.sample_data import SAMPLE_PROFILE as SAMPLE

COMMANDS = {"shacl": generate.gen_shacl, "puml": generate.gen_puml, "doc": generate.gen_doc}
FIRST_FILE = {"shacl": "shapes-default.ttl", "puml": "diagram-default.puml", "doc": "main.html"}


def invoke(command, *args):
    return CliRunner().invoke(command, [str(a) for a in args])


@pytest.mark.parametrize("name", sorted(COMMANDS))
def test_writes_its_representation(name, tmp_path):
    result = invoke(COMMANDS[name], SAMPLE, "-o", tmp_path)
    assert result.exit_code == 0, result.output
    assert (tmp_path / FIRST_FILE[name]).is_file()


@pytest.mark.parametrize(
    "args, message",
    [
        (("missing.json",), "missing.json"),
        ((SAMPLE, "--threshold", "0"), "acceptance_threshold"),
        ((SAMPLE, "-o", "nowhere"), "not an existing folder"),
        ((SAMPLE, "--template", "nowhere"), "not a template package"),
    ],
)
def test_usage_errors_exit_2(tmp_path, args, message):
    args = tuple(tmp_path / a if isinstance(a, str) and a in ("missing.json", "nowhere") else a for a in args)
    if "-o" not in args:
        args += ("-o", tmp_path)
    result = invoke(generate.gen_shacl, *args)
    assert result.exit_code == 2 and message in result.output


def test_the_threshold_changes_the_shapes(tmp_path):
    strict, loose = tmp_path / "strict", tmp_path / "loose"
    strict.mkdir(), loose.mkdir()
    invoke(generate.gen_shacl, SAMPLE, "-o", strict, "--threshold", "1")
    invoke(generate.gen_shacl, SAMPLE, "-o", loose, "--threshold", "0.5")

    def shapes(folder):
        return {f.name: f.read_text() for f in folder.iterdir()}

    assert shapes(strict).keys() == shapes(loose).keys() and shapes(strict) != shapes(loose)


def test_shapes_namespace(tmp_path):
    invoke(generate.gen_shacl, SAMPLE, "-o", tmp_path, "--shapes-namespace", "https://shapes.ex/")
    assert "<https://shapes.ex/" in (tmp_path / "shapes-default.ttl").read_text()


def test_a_custom_template_package(tmp_path):
    package = tmp_path / "mine"
    (package / "templates").mkdir(parents=True)
    (package / "templates" / "out.ttl").write_text("# {{ conf.title }}\n")
    (package / "config.json").write_text(json.dumps({"template": "out.ttl", "conf": {"title": "Ours"}}))
    result = invoke(generate.gen_shacl, SAMPLE, "-o", tmp_path, "--template", package)
    assert result.exit_code == 0 and (tmp_path / "shapes-default.ttl").read_text() == "# Ours"


def test_invalid_generated_turtle_exits_4_and_writes_nothing(tmp_path):
    package = tmp_path / "broken"
    (package / "templates").mkdir(parents=True)
    (package / "templates" / "out.ttl").write_text("<urn:a> <urn:b\n")
    (package / "config.json").write_text(json.dumps({"template": "out.ttl", "conf": {}}))
    out = tmp_path / "out"
    out.mkdir()
    result = invoke(generate.gen_shacl, SAMPLE, "-o", out, "--template", package)
    assert result.exit_code == 4 and not list(out.iterdir())


def test_an_unwritable_shapes_namespace_is_a_usage_error(tmp_path):
    result = invoke(generate.gen_shacl, SAMPLE, "-o", tmp_path, "--shapes-namespace", "urn:a b")
    assert result.exit_code == 2 and "cannot be written as an IRI" in result.output


def test_a_profile_with_failures_still_generates(tmp_path):
    from fingerprint.adapters.profile_file import save_profile
    from fingerprint.domain.profile import Failure, QueryKind
    from tests.builders import klass, profile_run
    from tests.fakes import EX

    failure = Failure(query_kind=QueryKind.co_types, class_iri=EX + "Big", message="not profiled")
    path = save_profile(profile_run(klass(EX + "Person", 2), failures=[failure]), tmp_path)
    out = tmp_path / "out"
    out.mkdir()
    result = invoke(generate.gen_doc, path, "-o", out)
    assert result.exit_code == 0 and "not profiled" in (out / "main.html").read_text()


def test_a_template_error_exits_4_and_names_the_template(tmp_path):
    package = tmp_path / "broken"
    (package / "templates").mkdir(parents=True)
    (package / "templates" / "broken.ttl").write_text("{{ view | no_such_filter }}")
    (package / "config.json").write_text(json.dumps({"template": "broken.ttl", "conf": {}}))
    result = invoke(generate.gen_shacl, SAMPLE, "-o", tmp_path, "--template", package)
    assert result.exit_code == 4 and "no_such_filter" in result.output


# --- llm-schema-tools: the pattern command (TC-E1) ---

LABELS = Path(__file__).parents[2] / "test_data" / "ontology" / "labels.ttl"


def test_the_pattern_command_writes_one_file_per_graph(tmp_path):
    result = invoke(generate.gen_pattern, SAMPLE, "-o", tmp_path)
    assert result.exit_code == 0, result.output
    assert (tmp_path / "pattern-continents-214e8f67.txt").is_file()


@pytest.mark.parametrize("option", ["--min-instances", "--max-classes"])
def test_a_size_filter_below_one_exits_2(tmp_path, option):
    result = invoke(generate.gen_pattern, SAMPLE, "-o", tmp_path, option, "0")
    assert result.exit_code == 2 and not list(tmp_path.iterdir())


def test_the_ontology_option_is_passed_through(tmp_path):
    result = invoke(generate.gen_pattern, SAMPLE, "-o", tmp_path, "--ontology", LABELS)
    assert result.exit_code == 0, result.output
    assert 'skos:Concept "Concept"@en' in (tmp_path / "pattern-continents-214e8f67.txt").read_text()


def test_the_size_options_are_passed_through(tmp_path):
    invoke(generate.gen_pattern, SAMPLE, "-o", tmp_path, "--max-classes", "1")
    blocks = [ln for ln in (tmp_path / "pattern-continents-214e8f67.txt").read_text().splitlines() if ln.startswith("(:")]
    assert len(blocks) == 1
