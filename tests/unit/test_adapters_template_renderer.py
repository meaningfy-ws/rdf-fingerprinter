"""The template renderer adapter: eds4jinja2 rendering, the Turtle check and check-then-write (P-1)."""

import json

import pytest

from fingerprint.adapters.exceptions import GeneratedOutputError, TemplatePackageError
from fingerprint.adapters.template_renderer import JinjaTemplateRenderer
from fingerprint.domain.views import Annotation, OutputCheck


def package(tmp_path, body, config=None):
    (tmp_path / "templates").mkdir(parents=True)
    (tmp_path / "templates" / "out.txt").write_text(body)
    (tmp_path / "config.json").write_text(json.dumps(config or {"template": "out.txt", "conf": {"title": "T"}}))
    return tmp_path


def texts(documents):
    return [d.text for d in documents]


def test_renders_each_output_with_its_view_and_the_configuration(tmp_path):
    renderer = JinjaTemplateRenderer()
    outputs = [("a.txt", Annotation(predicate="p", value="1")), ("b.txt", Annotation(predicate="q", value="2"))]
    documents = renderer.render(package(tmp_path, "{{ conf.title }} {{ view.value }}"), outputs, conf={"x": 1})
    assert [(d.file_name, d.text) for d in documents] == [("a.txt", "T 1"), ("b.txt", "T 2")]


def test_conf_is_merged_over_the_package_configuration(tmp_path):
    renderer = JinjaTemplateRenderer()
    assert texts(renderer.render(package(tmp_path, "{{ conf.title }}"), [("a", None)], conf={"title": "U"})) == ["U"]


@pytest.mark.parametrize("autoescape, shown", [(True, "&lt;b&gt;"), (False, "<b>")])
def test_autoescape_is_chosen_by_the_caller(tmp_path, autoescape, shown):
    view = Annotation(predicate="p", value="<b>")
    rendered = JinjaTemplateRenderer().render(package(tmp_path, "{{ view.value }}"), [("a", view)], autoescape=autoescape)
    assert texts(rendered) == [shown]


def test_a_configuration_without_template_is_a_package_error(tmp_path):
    with pytest.raises(TemplatePackageError, match="config.json must have"):
        JinjaTemplateRenderer().render(package(tmp_path, "x", config={"conf": {}}), [("a", None)])


def test_make_writes_every_output(tmp_path):
    body = "{% if view %}<urn:a> <urn:b> <urn:c> .{% endif %}"
    outputs = [("a.ttl", Annotation(predicate="p", value="v")), ("b.txt", None)]
    paths = JinjaTemplateRenderer().make(package(tmp_path / "p", body), outputs, folder=tmp_path / "out")
    assert [p.name for p in paths] == ["a.ttl", "b.txt"] and (tmp_path / "out" / "b.txt").read_text() == ""


def test_invalid_turtle_writes_nothing(tmp_path):
    body = "{% if view %}<urn:a> <urn:b> <urn:c> .{% else %}<urn:a> <urn:b{% endif %}"
    outputs = [("good.ttl", Annotation(predicate="p", value="v")), ("bad.ttl", None)]
    with pytest.raises(GeneratedOutputError, match="bad.ttl is not valid turtle"):
        JinjaTemplateRenderer().make(package(tmp_path / "p", body), outputs, folder=tmp_path / "out", check=OutputCheck.turtle)
    assert not (tmp_path / "out").exists()


def test_the_filters_escape_for_custom_templates(tmp_path):
    body = "{{ view.predicate | turtle_term }} {{ view.value | turtle_string }} {{ view.predicate | curie }}"
    renderer = JinjaTemplateRenderer(prefixes={"ex": "http://ex.org/"})
    view = Annotation(predicate="http://ex.org/a", value='say "x"')
    assert texts(renderer.render(package(tmp_path, body), [("a", view)])) == ['ex:a "say \\"x\\"" ex:a']


def test_the_packaged_prefixes_are_loaded_once_without_colons():
    prefixes = JinjaTemplateRenderer().prefixes
    assert prefixes["skos"] == "http://www.w3.org/2004/02/skos/core#" and not any(p.endswith(":") for p in prefixes)
