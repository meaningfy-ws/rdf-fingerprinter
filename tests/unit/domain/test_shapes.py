"""Shape IRI policy (profile-representations › Shape IRI policy)."""

import pytest

from fingerprint.domain.prefixes import PrefixTable
from fingerprint.domain.profile import NamespacePrefix, PrefixSource
from fingerprint.domain.shapes import shape_iri

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
