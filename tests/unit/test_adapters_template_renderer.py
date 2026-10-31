"""The template renderer adapter: eds4jinja2 rendering, the Turtle check and check-then-write (P-1)."""

import json

import pytest
from eds4jinja2.services.report_builder import ReportBuilder

from fingerprint.adapters.exceptions import GeneratedOutputError, TemplatePackageError
from fingerprint.adapters.template_renderer import JinjaTemplateRenderer
from fingerprint.domain.views import Annotation, RenderedDocument


def package(tmp_path, body, config=None):
    (tmp_path / "templates").mkdir(parents=True)
    (tmp_path / "templates" / "out.txt").write_text(body)
    (tmp_path / "config.json").write_text(json.dumps(config or {"template": "out.txt", "conf": {"title": "T"}}))
    return tmp_path


def test_report_builder_exposes_template_env(tmp_path):
    builder = ReportBuilder(target_path=package(tmp_path, "x"))
    assert builder.template == "out.txt" and builder.template_env.get_template("out.txt").render() == "x"


def test_renders_the_view_and_the_configuration(tmp_path):
    text = JinjaTemplateRenderer().render(package(tmp_path, "{{ conf.title }} {{ view.n }}"), view={"n": 3})
    assert text == "T 3"


@pytest.mark.parametrize("autoescape, shown", [(True, "&lt;b&gt;"), (False, "<b>")])
def test_autoescape_is_chosen_by_the_caller(tmp_path, autoescape, shown):
    renderer = JinjaTemplateRenderer()
    assert renderer.render(package(tmp_path, "{{ view }}"), view="<b>", autoescape=autoescape) == shown


def test_a_configuration_without_template_is_a_package_error(tmp_path):
    with pytest.raises(TemplatePackageError, match="config.json must have"):
        JinjaTemplateRenderer().render(package(tmp_path, "x", config={"conf": {}}))


def test_writes_every_text(tmp_path):
    documents = [
        RenderedDocument(file_name="a.ttl", text="<urn:a> <urn:b> <urn:c> .\n"),
        RenderedDocument(file_name="b.txt", text="b"),
    ]
    paths = JinjaTemplateRenderer().write(tmp_path, documents)
    assert [p.name for p in paths] == ["a.ttl", "b.txt"] and (tmp_path / "b.txt").read_text() == "b"


def test_invalid_turtle_writes_nothing(tmp_path):
    texts = [
        RenderedDocument(file_name="good.ttl", text="<urn:a> <urn:b> <urn:c> .\n"),
        RenderedDocument(file_name="bad.ttl", text="<urn:a> <urn:b"),
    ]
    with pytest.raises(GeneratedOutputError, match="bad.ttl"):
        JinjaTemplateRenderer().write(tmp_path, texts, check="turtle")
    assert not list(tmp_path.iterdir())


def test_the_filters_escape_for_custom_templates(tmp_path):
    body = "{{ view.predicate | turtle_term }} {{ view.value | turtle_string }} {{ view.predicate | curie }}"
    renderer = JinjaTemplateRenderer(prefixes={"ex": "http://ex.org/"})
    view = Annotation(predicate="http://ex.org/a", value='say "x"')
    assert renderer.render(package(tmp_path, body), view=view) == 'ex:a "say \\"x\\"" ex:a'


def test_the_packaged_prefixes_are_loaded_once_without_colons():
    prefixes = JinjaTemplateRenderer().prefixes
    assert prefixes["skos"] == "http://www.w3.org/2004/02/skos/core#" and not any(p.endswith(":") for p in prefixes)
