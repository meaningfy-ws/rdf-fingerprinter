"""Shape IRI policy (profile-representations › Shape IRI policy; readable-representations DEC-6). Pure."""

from fingerprint.domain.prefixes import PrefixTable, namespace_of


def _split(iri: str, table: PrefixTable) -> tuple[str, str, str]:
    """(namespace, prefix, local part, `_` when empty) of an IRI by the table."""
    entry = table.entry_for(iri)
    namespace = entry.namespace if entry else namespace_of(iri)
    prefix = entry.prefix if entry else "ns"
    return namespace, prefix, iri[len(namespace) :] or "_"


def shapes_base(class_namespace: str) -> str:
    """`<namespace without its trailing # / :>/shape/`, or `…:shape:` for a URN namespace."""
    base = class_namespace.rstrip("#/:")
    return base + (":shape:" if class_namespace.startswith("urn:") and "/" not in class_namespace else "/shape/")


def shape_iri(
    class_iri: str, property_iri: str | None, table: PrefixTable, shapes_namespace: str | None
) -> tuple[str, str, str]:
    """(shape IRI, its prefix, the prefix's namespace) of a class's node shape, or of one of its property shapes."""
    namespace, prefix, local = _split(class_iri, table)
    if shapes_namespace:
        name, shape_prefix, shape_namespace = f"{prefix}-{local}", "shape", shapes_namespace
    else:
        name, shape_prefix, shape_namespace = local, f"{prefix}-shape", shapes_base(namespace)
    if property_iri is not None:
        _, p_prefix, p_local = _split(property_iri, table)
        name = f"{name}-{p_prefix}-{p_local}"
    return shape_namespace + name, shape_prefix, shape_namespace
