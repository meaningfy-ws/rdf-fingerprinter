"""PlantUML class diagrams: an overview and modules per graph (profile-representations › PlantUML class diagram)."""

import re

from fingerprint.adapters.template_renderer import JinjaTemplateRenderer
from fingerprint.domain.analytics import analyse
from fingerprint.domain.profile import NamespacePrefix
from fingerprint.domain.views import GeneratorOptions
from fingerprint.service_layer.generators.plantuml import PlantumlGenerator
from tests import builders
from tests.builders import klass, literals, profile_run, prop, resources
from tests.fakes import EX, files

FOAF = "http://xmlns.com/foaf/0.1/"
OWL = "http://www.w3.org/2002/07/owl#"


def outputs(run, **options):
    generator = PlantumlGenerator(analyse(run), JinjaTemplateRenderer(), options=GeneratorOptions(**options))
    return files(generator.serialize()), generator


def diagram(run, **options):
    """The module files' text, joined, and the generator."""
    texts, generator = outputs(run, **options)
    return "\n".join(t for name, t in sorted(texts.items()) if "--" in name), generator


def aliases(text):
    return dict(re.findall(r'class "([^"]+)" as (\w+)', text))


def test_an_overview_and_a_module_per_namespace_each_between_start_and_end():
    texts, _ = outputs(profile_run(klass(EX + "Person", 4), klass(FOAF + "Agent", 1)))
    assert sorted(texts) == ["diagram-default--ex.puml", "diagram-default--foaf.puml", "diagram-default.puml"]
    for text in texts.values():
        assert text.count("@startuml") == 1 and text.count("@enduml") == 1 and text.strip().endswith("@enduml")


def test_the_overview_counts_links_between_namespaces():
    targets = [klass(EX + f"C{n}", 2, prop(EX + "knows", {1: 2}, resources(2, FOAF + "Person"))) for n in range(3)]
    texts, _ = outputs(profile_run(*targets))
    overview = texts["diagram-default.puml"]
    assert 'package "ex (3 classes)" as N1' in overview and 'package "foaf (referenced)" as N2' in overview
    assert "N1 --> N2 : 3" in overview


def test_a_big_namespace_is_split_into_clusters():
    run = profile_run(*(klass(EX + f"C{n:02}", 1) for n in range(7)))
    texts, _ = outputs(run, module_size=3)
    assert sorted(n for n in texts if "--" in n) == [f"diagram-default--ex~{n}.puml" for n in (1, 2, 3)]
    assert outputs(run, module_size=3)[0] == texts


def test_a_class_outside_the_module_is_a_reference_box():
    run = profile_run(klass(EX + "Person", 4, prop(EX + "knows", {1: 4}, resources(4, FOAF + "Person"))))
    text, _ = diagram(run)
    assert 'class "foaf:Person" as P1 #lightgray' in text and '--> "1" P1 : ex:knows' in text


def test_meta_classes_are_hidden_unless_included_and_empty_graphs_write_nothing():
    run = profile_run(klass(OWL + "Ontology", 1))
    assert outputs(run)[0] == {}
    assert "diagram-default--owl.puml" in outputs(run, include_namespaces=["owl"])[0]


def test_class_with_an_attribute_and_an_implied_parent():
    run = profile_run(klass(EX + "Person", 4, prop(EX + "name", {1: 4}, literals(4)), co_types=[(EX + "Agent", 4)]))
    text, _ = diagram(run)
    names = aliases(text)
    assert list(names).count("ex:Person") == 1
    assert "ex:name : xsd:string [1]" in text
    assert f"{names['ex:Person']} ..|> {names['ex:Agent']}" in text


def test_declared_parent_is_a_solid_generalisation():
    run = profile_run(klass(EX + "Person", 4), klass(EX + "Agent", 4), edges=[(EX + "Person", EX + "Agent")])
    text, _ = diagram(run)
    names = aliases(text)
    assert f"{names['ex:Person']} --|> {names['ex:Agent']}" in text


def test_object_property_to_one_profiled_class_is_an_association():
    run = profile_run(
        klass(EX + "Person", 4, prop(EX + "livesIn", {1: 2}, resources(2, EX + "City"))),
        klass(EX + "City", 2),
    )
    text, _ = diagram(run)
    names = aliases(text)
    assert f'{names["ex:Person"]} --> "0..1" {names["ex:City"]} : ex:livesIn' in text
    assert "ex:livesIn :" not in text


def test_object_property_to_untyped_objects_stays_an_attribute():
    text, _ = diagram(profile_run(klass(EX + "Person", 4, prop(EX + "knows", {2: 4}, resources(8)))))
    assert "ex:knows : resource [2]" in text


def test_inherited_properties_are_not_repeated():
    run = profile_run(
        klass(EX + "Agent", 4, prop(EX + "name", {1: 4}, literals(4))),
        klass(EX + "Person", 4, prop(EX + "name", {1: 4}, literals(4))),
        edges=[(EX + "Person", EX + "Agent")],
    )
    text, _ = diagram(run)
    assert text.count("ex:name : xsd:string [1]") == 1


def test_unusual_and_unwritable_iris():
    bad = "http://ex.org/<script> x"
    run = profile_run(klass("http://ex.org/q?a=1&b='x'", 4, prop("http://ex.org/ș/ü", {1: 4}, literals(4))), klass(bad, 1))
    text, generator = diagram(run)
    assert len(aliases(text)) == 1 and "script" not in text and generator.skipped == [bad]


def test_an_unwritable_value_type_never_reaches_the_diagram():
    evil = "http://x/a\n}\n!include /etc/hostname\nclass X {"
    run = profile_run(klass(EX + "Person", 4, prop(EX + "p", {1: 4}, literals(4, datatype=evil))))
    text, generator = diagram(run)
    assert "!include" not in text and evil in generator.skipped
    assert "ex:p : value [1]" in text


def test_a_graph_label_is_plain_text_in_the_title():
    run = profile_run(klass(EX + "Person", 4), graph='http://g/%getenv("HOME")\n!include x')
    text, _ = diagram(run)
    (title,) = [line for line in text.splitlines() if line.startswith("title ")]
    assert "%" not in title and '"' not in title and "!include" not in text


def test_a_prefix_that_looks_like_a_cluster_name_keeps_its_own_module():
    namespaces = [
        NamespacePrefix(prefix="ex", namespace="http://ex.org/", source="user"),
        NamespacePrefix(prefix="ex-1", namespace="http://ex.org/1/", source="user"),
    ]
    big = profile_run(*(klass(f"http://ex.org/C{n}", 1) for n in range(4)), klass("http://ex.org/1/D", 1))
    texts, _ = outputs(big.model_copy(update={"namespaces": namespaces}), module_size=2)
    modules = sorted(n for n in texts if "--" in n)
    assert modules == ["diagram-default--ex-1.puml", "diagram-default--ex~1.puml", "diagram-default--ex~2.puml"]


# --- decisions the first tests left open (lean-test-suite 7.5) ---


def with_prefixes(run, **namespace_of_prefix):
    """`run` with a user prefix table: {prefix: namespace}."""
    table = [NamespacePrefix(prefix=p, namespace=ns, source="user") for p, ns in namespace_of_prefix.items()]
    return run.model_copy(update={"namespaces": table})


def test_classes_get_aliases_from_c1_in_iri_order():
    text, _ = diagram(profile_run(klass(EX + "B", 1), klass(EX + "A", 1)))
    assert aliases(text) == {"ex:A": "C1", "ex:B": "C2"}


def test_a_custom_template_location_replaces_the_packaged_template(tmp_path):
    (tmp_path / "templates").mkdir()
    (tmp_path / "templates" / "out.txt").write_text("custom")
    (tmp_path / "config.json").write_text('{"template": "out.txt", "conf": {}}')
    generator = PlantumlGenerator(analyse(profile_run(klass(EX + "A", 1))), JinjaTemplateRenderer(), tmp_path)
    assert set(files(generator.serialize()).values()) == {"custom"}


def test_a_namespace_is_one_module_up_to_fifteen_classes_by_default():
    def modules(n):
        texts, _ = outputs(profile_run(*(klass(EX + f"C{i:02}", 1) for i in range(n))))
        return [name for name in texts if "--" in name]

    assert modules(15) == ["diagram-default--ex.puml"]
    assert modules(16) == ["diagram-default--ex~1.puml", "diagram-default--ex~2.puml"]


def test_no_module_size_means_fifteen():
    texts, _ = outputs(profile_run(*(klass(EX + f"C{i:02}", 1) for i in range(16))), module_size=None)
    assert sorted(n for n in texts if "--" in n) == ["diagram-default--ex~1.puml", "diagram-default--ex~2.puml"]


def test_files_follow_the_prefix_order_of_their_namespaces():
    run = with_prefixes(
        profile_run(klass("http://a.org/A", 1), klass("http://b.org/B", 1)), zz="http://a.org/", aa="http://b.org/"
    )
    assert list(outputs(run)[0]) == ["diagram-default.puml", "diagram-default--aa.puml", "diagram-default--zz.puml"]


def test_parents_are_listed_in_iri_order_declared_or_implied():
    run = profile_run(
        klass(EX + "Person", 4, co_types=[(EX + "Agent", 4)]), klass(EX + "Zoo", 1), edges=[(EX + "Person", EX + "Zoo")]
    )
    text, _ = diagram(run)
    names = aliases(text)
    implied, declared = f"{names['ex:Person']} ..|> {names['ex:Agent']}", f"{names['ex:Person']} --|> {names['ex:Zoo']}"
    assert text.index(implied) < text.index(declared)


def test_a_hidden_or_unwritable_parent_is_left_out():
    run = profile_run(klass(EX + "Person", 4, co_types=[(OWL + "Thing", 4), ("http://ex.org/a b", 4)]))
    text, generator = diagram(run)
    assert "|>" not in text and generator.skipped == ["http://ex.org/a b"]


def test_a_graph_names_the_files_and_the_titles():
    texts, _ = outputs(profile_run(klass(EX + "A", 1), graph="http://ex.org/graphs/people"))
    assert all(re.fullmatch(r"diagram-people-[0-9a-f]{8}(--ex)?\.puml", name) for name in texts) and len(texts) == 2
    titles = {line for text in texts.values() for line in text.splitlines() if line.startswith("title ")}
    assert all("graphs:people" in title for title in titles)


def test_every_file_lists_every_iri_skipped():
    bad = "http://ex.org/a b"
    generator = PlantumlGenerator(analyse(profile_run(klass(EX + "A", 1), klass(bad, 1))), JinjaTemplateRenderer())
    views = generator.outputs()
    assert len(views) == 2 and [view.skipped for _, view in views] == [[bad], [bad]]


def test_namespaces_are_ordered_by_prefix_not_by_iri():
    run = with_prefixes(
        profile_run(klass("http://a.org/A", 1), klass("http://b.org/B", 1)), zz="http://a.org/", aa="http://b.org/"
    )
    texts, _ = outputs(run)
    overview = texts["diagram-default.puml"]
    assert overview.index('package "aa (1 classes)" as N1') < overview.index('package "zz (1 classes)" as N2')


def test_a_namespace_missing_from_the_table_is_named_by_its_iri():
    run = with_prefixes(profile_run(klass(EX + "A", 1, prop(EX + "p", {1: 1}, resources(1, FOAF + "P")))), ex=EX)
    assert f'package "{FOAF} (referenced)"' in outputs(run)[0]["diagram-default.puml"]


def test_each_reference_gets_its_own_alias_and_boxes_follow_alias_order():
    """A profiled class of another module (C…) comes before the unprofiled ones (P1, …, P11), numerically."""
    others = [prop(EX + f"p{n:02}", {1: 1}, resources(1, FOAF + f"T{n:02}")) for n in range(11)]
    run = profile_run(
        klass(EX + "A", 1, *others, prop(EX + "q", {1: 1}, resources(1, FOAF + "Agent"))), klass(FOAF + "Agent", 1)
    )
    texts, _ = outputs(run)
    boxes = re.findall(r'class "[^"]+" as (\w+) #lightgray', texts["diagram-default--ex.puml"])
    assert boxes == ["C2"] + [f"P{n}" for n in range(1, 12)]


def test_a_link_to_a_hidden_class_is_not_counted_and_the_others_still_are():
    run = profile_run(
        klass(EX + "A", 1, prop(EX + "p", {1: 1}, resources(1, OWL + "Class"))),
        klass(EX + "B", 1, prop(EX + "p", {1: 1}, resources(1, FOAF + "Person"))),
    )
    overview = outputs(run)[0]["diagram-default.puml"]
    assert "N1 --> N2 : 1" in overview and "owl" not in overview


def test_overview_packages_list_their_modules_and_links_are_ordered_by_prefix():
    run = with_prefixes(
        profile_run(
            klass(
                "http://1/N",
                1,
                prop("http://1/p1", {1: 1}, resources(1, "http://3/T")),
                prop("http://1/p2", {1: 1}, resources(1, "http://4/T")),
            ),
            klass(
                "http://2/M",
                1,
                prop("http://2/p1", {1: 1}, resources(1, "http://3/T")),
                prop("http://2/p2", {1: 1}, resources(1, "http://4/T")),
            ),
        ),
        n="http://1/",
        m="http://2/",
        b="http://3/",
        a="http://4/",
    )
    overview = outputs(run)[0]["diagram-default.puml"]
    assert "  [m]" in overview and "  [n]" in overview
    packages = dict(re.findall(r'package "(\w+) [^"]*" as (N\d)', overview))
    arrows = [(a, b) for a, b in re.findall(r"(N\d) --> (N\d) : 1", overview)]
    named = {alias: prefix for prefix, alias in packages.items()}
    assert [(named[a], named[b]) for a, b in arrows] == [("m", "a"), ("m", "b"), ("n", "a"), ("n", "b")]


def test_a_big_namespace_lists_its_clusters_in_the_overview():
    run = profile_run(*(klass(EX + f"C{n:02}", 1) for n in range(7)))
    overview = outputs(run, module_size=3)[0]["diagram-default.puml"]
    assert all(f"  [ex~{n}]" in overview for n in (1, 2, 3))


def test_value_types_are_joined_and_an_untyped_part_adds_resource():
    typed = prop(EX + "a", {1: 4}, literals(2), literals(2, datatype="http://www.w3.org/2001/XMLSchema#integer"))
    mixed = prop(EX + "b", {1: 4}, resources(2, EX + "City"), resources(2))
    unwritable = prop(EX + "c", {1: 4}, resources(4, "http://x/a b"))
    text, _ = diagram(profile_run(klass(EX + "Person", 4, typed, mixed, unwritable)))
    assert "ex:a : xsd:integer | xsd:string [1]" in text
    assert "ex:b : ex:City | resource [1]" in text
    assert "ex:c : resource [1]" in text


def test_every_diagram_file_notes_the_excluded_namespaces_after_the_start_and_none_without_a_filter():
    def texts(analytics):
        return files(PlantumlGenerator(analytics, JinjaTemplateRenderer()).serialize())

    noted = texts(builders.filtered_analytics("rel"))
    assert len(noted) > 1
    assert all(t.splitlines()[1] == f"' excluded namespaces: {builders.REL_NOTE}" for t in noted.values())
    assert not any("excluded namespaces" in t for t in texts(builders.filtered_analytics("foaf")).values())
