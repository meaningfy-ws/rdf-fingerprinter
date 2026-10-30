"""Report generation against the loaded test store (`make oxigraph-load-test-data`)."""

from pathlib import Path

from bs4 import BeautifulSoup

from fingerprint.service_layer.handlers import generate_endpoint_fingerprint_report
from tests import LOCAL_ENDPOINT


def test_generate_endpoint_fingerprint_report_default_template(tmpdir):
    """
        given  an input endpoint
        when generate is executed
        the output folder has a report file
    :return:
    """
    output_path = tmpdir.mkdir("/output")

    output_file = generate_endpoint_fingerprint_report(sparql_endpoint_url=LOCAL_ENDPOINT, output_location=str(output_path))

    with open(output_file) as file:
        soup = BeautifulSoup(file.read(), "html.parser")

    # strict stores (Oxigraph) leave unbound cells when the SPARQL is not portable (DEC-11)
    assert "nan" not in [cell.text.strip() for cell in soup.find_all("td")]

    main_title = soup.find("h1", attrs={"id": "skip-toc"}).text
    assert main_title == "Structural fingerprint"

    tables = soup.find_all("table")
    assert len(tables) == 6

    classes_list = [
        "owl#Ontology",
        "core#ConceptScheme",
        "skos-xl#Label",
        "core#Concept",
        "euvoc#Continent",
        "euvoc#XlNotation",
    ]

    for class_name in classes_list:
        assert any(class_name in table.text for table in tables)


def test_generate_endpoint_fingerprint_report_custom_template(tmpdir):
    output_path = tmpdir.mkdir("/output")

    custom_template_location = Path(__file__).parents[1] / "test_data/custom_template"
    output_file = generate_endpoint_fingerprint_report(
        sparql_endpoint_url=LOCAL_ENDPOINT,
        output_location=str(output_path),
        external_template_location=custom_template_location,
    )

    with open(output_file) as file:
        soup = BeautifulSoup(file.read(), "html.parser")

    main_title = soup.find("h1").text
    assert main_title == "Test structural fingerprint"
