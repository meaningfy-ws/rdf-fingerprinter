"""Report generation against the loaded test store (`make oxigraph-load-test-data`)."""

from pathlib import Path

from bs4 import BeautifulSoup

from fingerprint.domain.views import GeneratorOptions
from fingerprint.service_layer.handlers import fingerprint_report
from fingerprint.service_layer.settings import resolve_settings
from tests import LOCAL_ENDPOINT

CLASSES = ["skos:ConceptScheme", "skosxl:Label", "skos:Concept", "euvoc:Continent", "euvoc:XlNotation"]


def report(output, **kwargs):
    path, _ = fingerprint_report(LOCAL_ENDPOINT, output, resolve_settings(), **kwargs)
    return BeautifulSoup(path.read_text(), "html.parser")


def test_the_report_page_on_the_test_store(tmp_path):
    soup = report(tmp_path)
    # strict stores (Oxigraph) leave unbound cells when the SPARQL is not portable (DEC-11)
    assert "nan" not in [cell.text.strip() for cell in soup.find_all("td")]
    assert soup.find("h1").contents[0].strip() == "RDF fingerprint"
    # the default graph and both named graphs (DEC-11): 6 + 6 + 7 classes, owl:Ontology hidden in each (DEC-8)
    sections = soup.select("details.cls")
    assert len(sections) == 16
    for name in CLASSES:
        assert any(name == s.find("h3").get_text() for s in sections), name
    assert "owl" in soup.find(id="caveats").get_text(" ")


def test_meta_classes_can_be_shown_again(tmp_path):
    soup = report(tmp_path, options=GeneratorOptions(include_namespaces=["owl"]))
    assert len(soup.select("details.cls")) == 19


def test_a_custom_template_package(tmp_path):
    soup = report(tmp_path, template=Path(__file__).parents[1] / "test_data/custom_template")
    assert soup.find("h1").text == "Ours" and soup.find(id="graphs").text == "3"
