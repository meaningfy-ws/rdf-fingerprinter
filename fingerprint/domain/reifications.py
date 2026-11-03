"""How a reified relation reads in every output (singleton-property-pattern P-11). Pure: no I/O.

One formatter, so the report, the pattern schema, ShExC, SHACL and PlantUML print the same text.
"""

from collections.abc import Callable

from fingerprint.domain.profile import ReificationCount, ReificationKind, ReifiedRelation
from fingerprint.domain.views import ReifiedRelationView

KIND_LABELS = {
    ReificationKind.rdf_statement: "RDF statement",
    ReificationKind.resource_as_predicate: "resource as predicate",
    ReificationKind.owl_axiom: "OWL axiom",
    ReificationKind.negative_property_assertion: "negative property assertion",
    ReificationKind.triple_term: "triple term",
    ReificationKind.graph_statement: "graph statement",
    ReificationKind.nanopublication: "nanopublication",
    ReificationKind.prov_qualified: "PROV qualified",
    ReificationKind.dcat_qualified: "DCAT qualified",
    ReificationKind.schema_role: "schema.org role",
    ReificationKind.wikibase_statement: "Wikibase statement",
    ReificationKind.cidoc_property_of_property: "CIDOC property of property",
}  # dict-ok: module-level lookup table
UNNAMED = "unnamed"


def relation_view(relation: ReifiedRelation, name: Callable[[str], str | None]) -> ReifiedRelationView | None:
    """The view of `relation`, its IRIs written by `name`; None when its property or object class cannot be written
    (an unwritable reifier property is left out of the list)."""
    prop = name(relation.property) if relation.property else UNNAMED
    object_class = name(relation.object_class) if relation.object_class else None
    if prop is None or (relation.object_class and object_class is None):
        return None
    reifiers = [(n, r.reifiers) for r in relation.reifier_properties or [] if (n := name(r.property)) is not None]
    reifier_text = ", ".join(f"{n} {count}" for n, count in reifiers) or None
    noun = "statement" if relation.statements == 1 else "statements"
    text = f"~> {prop} (:{object_class or '?'}) {relation.statements} {noun} via {ReificationKind(relation.kind).value}"
    return ReifiedRelationView(
        kind=KIND_LABELS[ReificationKind(relation.kind)],
        property=prop,
        object_class=object_class,
        statements=relation.statements,
        reifier_text=reifier_text,
        text=f"{text} [reifiers: {reifier_text}]" if reifier_text else text,
    )


def reification_note(kinds: list[ReificationKind] | None, counts: list[ReificationCount] | None) -> str | None:
    """The graph summary line: the kinds found and each non-zero count ("1 triple term"); None when no kind was found."""
    if not kinds:
        return None
    names = ", ".join(sorted(KIND_LABELS[ReificationKind(k)] for k in kinds))
    counted = [
        f"{c.count} {KIND_LABELS[ReificationKind(c.kind)]}{'' if c.count == 1 else 's'}" for c in counts or [] if c.count
    ]
    return f"Reifications found: {names}" + (f"; {', '.join(counted)}." if counted else ".")
