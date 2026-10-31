import json

import pytest

from fingerprint.service_layer.settings import UsageError, load_config_file, resolve_settings


def test_defaults():
    s = resolve_settings(env={})
    assert (s.depth, s.precision_policy, s.first_n, s.top_k) == ("values", "auto", 10000, 20)
    assert (s.timeout_seconds, s.concurrency, s.acceptance_threshold) == (60, 4, 0.95)
    assert (s.object_type_scope, s.completeness_check, s.graph_statistics) == ("same_graph", False, False)
    assert not s.selected_graphs


@pytest.mark.parametrize(
    "env, cli, timeout",
    [
        ({}, {}, 60),
        ({"RDF_FINGERPRINTER_TIMEOUT_SECONDS": "10"}, {}, 10),
        ({"RDF_FINGERPRINTER_TIMEOUT_SECONDS": "10"}, {"timeout_seconds": 30}, 30),
    ],
)
def test_precedence_cli_over_env_over_default(env, cli, timeout):
    assert resolve_settings(cli=cli, env=env).timeout_seconds == timeout


def test_env_over_config_over_default():
    assert resolve_settings(env={}, config={"concurrency": 2}).concurrency == 2
    assert resolve_settings(env={"RDF_FINGERPRINTER_CONCURRENCY": "3"}, config={"concurrency": 2}).concurrency == 3


def test_selected_graphs_parameter_sits_between_env_and_config():
    assert resolve_settings(env={}, selected_graphs=["g1"], config={"selected_graphs": ["g2"]}).selected_graphs == ["g1"]
    env = {"RDF_FINGERPRINTER_SELECTED_GRAPHS": "a, b"}
    assert resolve_settings(env=env, selected_graphs=["g1"]).selected_graphs == ["a", "b"]


@pytest.mark.parametrize("value, expected", [("1", True), ("YES", True), ("on", True), ("0", False), ("Off", False)])
def test_boolean_env_values(value, expected):
    assert resolve_settings(env={"RDF_FINGERPRINTER_COMPLETENESS_CHECK": value}).completeness_check is expected


@pytest.mark.parametrize(
    "kwargs",
    [
        {"env": {"RDF_FINGERPRINTER_COMPLETENESS_CHECK": "maybe"}},
        {"env": {"RDF_FINGERPRINTER_FIRST_N": "many"}},
        {"env": {}, "config": {"bogus": 1}},
        {"env": {}, "cli": {"acceptance_threshold": 0}},
        {"env": {}, "cli": {"depth": "everything"}},
        {"env": {}, "cli": {"first_n": 0}},
    ],
)
def test_bad_values_are_usage_errors(kwargs):
    with pytest.raises(UsageError):
        resolve_settings(**kwargs)


def test_other_prefixed_variables_are_ignored():
    assert resolve_settings(env={"RDF_FINGERPRINTER_TEST_ENDPOINT": "x"}).depth == "values"


def test_config_file(tmp_path):
    path = tmp_path / "c.json"
    path.write_text(json.dumps({"concurrency": 2}))
    assert resolve_settings(env={}, config=load_config_file(path)).concurrency == 2
    path.write_text("[1]")
    with pytest.raises(UsageError):
        load_config_file(path)
