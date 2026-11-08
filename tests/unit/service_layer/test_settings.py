import json

import pytest
from pydantic import BaseModel, ValidationError, model_validator

from fingerprint.service_layer.settings import (
    UsageError,
    describe,
    load_config_file,
    load_user_prefixes,
    resolve_settings,
    validate_endpoint,
)


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


def test_config_file(tmp_path):
    path = tmp_path / "c.json"
    path.write_text(json.dumps({"concurrency": 2}))
    assert resolve_settings(env={}, config=load_config_file(path)).concurrency == 2
    path.write_text("[1]")
    with pytest.raises(UsageError):
        load_config_file(path)


def test_each_source_is_checked_on_its_own():
    """A malformed lower-precedence value fails even when a higher source sets it (domain-object-model P-7)."""
    with pytest.raises(UsageError):
        resolve_settings(cli={"concurrency": 2}, env={}, config={"concurrency": 0})


# --- the usage messages are the contract (lean-test-suite 7.5) ---


def test_an_unreadable_config_file_names_the_file(tmp_path):
    (tmp_path / "list.json").write_text("[1]")
    with pytest.raises(UsageError, match=f"^config file {tmp_path}/list.json must hold a JSON object$"):
        load_config_file(tmp_path / "list.json")
    with pytest.raises(UsageError, match=f"^cannot read config file {tmp_path}/none.json: "):
        load_config_file(tmp_path / "none.json")


@pytest.mark.parametrize(
    "kwargs, message",
    [
        ({"cli": {"acceptance_threshold": 0}}, "acceptance_threshold must be in (0, 1]"),
        (
            {"cli": {"depth": "x", "first_n": 0}},
            "depth: Input should be 'graphs', 'classes', 'properties', 'values', 'rich_values' or 'links'; "
            "first_n: Input should be greater than or equal to 1",
        ),
        ({"cli": {"bogus": 1}}, "bogus: Extra inputs are not permitted"),
        ({"config": {"concurrency": 0}}, "concurrency: Input should be greater than or equal to 1"),
        ({"config": {"zeta": 1, "alpha": 2}}, "unknown collection settings: alpha, zeta"),
        (
            {"env": {"RDF_FINGERPRINTER_FIRST_N": "many"}},
            "RDF_FINGERPRINTER_FIRST_N: Input should be a valid integer, unable to parse string as an integer",
        ),
    ],
    ids=["threshold", "two-fields", "cli-extra", "config-value", "unknown-keys", "environment"],
)
def test_a_bad_setting_is_one_line_naming_what_is_wrong(kwargs, message):
    with pytest.raises(UsageError) as error:
        resolve_settings(**{"env": {}, **kwargs})
    assert str(error.value) == message


def test_a_model_error_without_a_field_is_reported_as_a_value():
    class Model(BaseModel):
        @model_validator(mode="after")
        def never(self):
            raise ValueError("no")

    with pytest.raises(ValidationError) as error:
        Model()
    assert describe(error.value) == "value: Value error, no"


def test_only_http_endpoints_are_accepted_and_credentials_are_not_echoed():
    validate_endpoint("HTTPS://e/sparql")
    with pytest.raises(UsageError) as error:
        validate_endpoint("ftp://user:secret@h/x")
    assert str(error.value) == "the endpoint must be an http or https URL, not 'ftp://h/x'"


def test_user_prefixes_come_from_the_option_before_the_variable(tmp_path, monkeypatch):
    option, variable = tmp_path / "option.json", tmp_path / "variable.json"
    option.write_text('{"o:": "http://o.example/"}')
    variable.write_text('{"v:": "http://v.example/"}')
    monkeypatch.setenv("RDF_FINGERPRINTER_PREFIXES_FILE", str(variable))
    assert [(e.prefix, e.source) for e in load_user_prefixes(option)] == [("o", "user")]
    assert [(e.prefix, e.source) for e in load_user_prefixes()] == [("v", "user")]
    monkeypatch.delenv("RDF_FINGERPRINTER_PREFIXES_FILE")
    assert load_user_prefixes() == []


def test_a_bad_prefixes_source_is_named_in_the_error(tmp_path, monkeypatch):
    with pytest.raises(UsageError, match="^--prefixes: cannot read "):
        load_user_prefixes(tmp_path / "none.json")
    monkeypatch.setenv("RDF_FINGERPRINTER_PREFIXES_FILE", str(tmp_path / "none.json"))
    with pytest.raises(UsageError, match="^RDF_FINGERPRINTER_PREFIXES_FILE: cannot read "):
        load_user_prefixes()


def test_an_error_inside_a_list_names_the_field_and_the_position():
    with pytest.raises(UsageError) as error:
        resolve_settings(env={}, cli={"selected_graphs": [1]})
    assert str(error.value).startswith("selected_graphs.0: ")


def test_a_bad_variable_is_a_configuration_error_and_a_bad_url_is_not(monkeypatch):
    from fingerprint.service_layer.exceptions import ConfigurationError
    from fingerprint.service_layer.settings import validate_config

    monkeypatch.setenv("RDF_FINGERPRINTER_MAX_ANSWER_BYTES", "big")
    with pytest.raises(ConfigurationError, match="RDF_FINGERPRINTER_MAX_ANSWER_BYTES"):
        validate_config()
    with pytest.raises(ConfigurationError):
        resolve_settings(env={"RDF_FINGERPRINTER_FIRST_N": "many"})
    monkeypatch.delenv("RDF_FINGERPRINTER_MAX_ANSWER_BYTES")
    with pytest.raises(UsageError) as raised:
        validate_endpoint("ftp://x")
    assert not isinstance(raised.value, ConfigurationError)
    assert issubclass(ConfigurationError, UsageError)
