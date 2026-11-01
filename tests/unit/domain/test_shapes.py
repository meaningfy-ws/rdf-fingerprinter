"""Shape IRI policy (profile-representations › Shape IRI policy)."""

import pytest

from fingerprint.domain.prefixes import PrefixTable
from fingerprint.domain.profile import NamespacePrefix, PrefixSource
from fingerprint.domain.shapes import shape_iri, shapes_base

BF = "https://ontology.brainframe.com/2016/04/brainframe#"
TABLE = PrefixTable(
    [NamespacePrefix(prefix=p, namespace=ns, source=PrefixSource.generated) for p, ns in [("bf", BF), ("x", "urn:x:")]]
)


@pytest.mark.parametrize(
    ("cls", "given", "node", "prop"),
    [
        (BF + "Asset", None, ("https://ontology.brainframe.com/2016/04/brainframe/shape/Asset", "bf-shape"), "Asset-bf-name"),
        (BF + "Asset", "http://ex.org/shapes/", ("http://ex.org/shapes/bf-Asset", "shape"), "bf-Asset-bf-name"),
        ("urn:x:Asset", None, ("urn:x:shape:Asset", "x-shape"), "Asset-bf-name"),
        (BF, None, ("https://ontology.brainframe.com/2016/04/brainframe/shape/_", "bf-shape"), "_-bf-name"),
    ],
)
def test_shape_names(cls, given, node, prop):
    iri, prefix, namespace = shape_iri(cls, None, TABLE, given)
    assert (iri, prefix) == node and iri.startswith(namespace)
    prop_iri, prop_prefix, _ = shape_iri(cls, BF + "name", TABLE, given)
    assert prop_iri == namespace + prop and prop_prefix == prefix


def test_a_property_equal_to_its_namespace_uses_underscore():
    assert shape_iri(BF + "Asset", BF, TABLE, None)[0].endswith("/shape/Asset-bf-_")


@pytest.mark.parametrize(
    ("class_namespace", "base"),
    [
        ("http://ex.org/X/", "http://ex.org/X/shape/"),
        ("urn:x:", "urn:x:shape:"),
        ("urn:x/y:", "urn:x/y/shape/"),
        ("tag:ex:", "tag:ex/shape/"),
    ],
)
def test_shapes_base(class_namespace, base):
    assert shapes_base(class_namespace) == base


def test_a_class_under_a_broader_entry_takes_that_entry_namespace():
    table = PrefixTable([NamespacePrefix(prefix="ex", namespace="http://ex.org/", source=PrefixSource.packaged)])
    iri, prefix, _ = shape_iri("http://ex.org/a/b", None, table, None)
    assert (iri, prefix) == ("http://ex.org/shape/a/b", "ex-shape")


def test_a_class_without_an_entry_takes_its_own_namespace_and_the_ns_prefix():
    iri, prefix, _ = shape_iri("http://other.org/v/Thing", None, TABLE, None)
    assert (iri, prefix) == ("http://other.org/v/shape/Thing", "ns-shape")
