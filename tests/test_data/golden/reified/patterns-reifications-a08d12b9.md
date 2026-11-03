# Patterns of http://example.org/reifications

Prefixes: `prefixes-reifications-a08d12b9.md` · glossary: `glossary-reifications-a08d12b9.md`

Legend: (:A&B) n: classes with the same n instances · ~m first_n: statistics over the first m read · co C k: k also typed C · via (:S)-p: incoming links · -p-> (:T|U) object classes · IRI, BNODE untyped · . not collected · deeper indent: a blank node's own edges, statistics over all its instances, up to 3 hops · ^ expanded under another edge · … deeper than 3 hops · k/n instances having p (omitted: all) · ×a-b values per instance (omitted: 1) · bn blank nodes · @n languages, @tag one language · =v one value · lo..hi range · dN distinct values (omitted: all differ) · presence found, not measured

Hidden: 1 classes.

## ex:Person

```text
(:ex:Person) 3
~> ex:Link (:ex:Org) 2 statements via resource_as_predicate [reifiers: rdf:singletonPropertyOf 2, prov:wasAttributedTo 1]
~> ex:Procedure (:ex:Org) 1 statement via resource_as_predicate
~> ex:knows (:ex:Person) 1 statement via owl_axiom [reifiers: dcterms:source 1]
~> ex:knows (:ex:Person) 1 statement via rdf_statement [reifiers: dcterms:source 1]
~> ex:worksFor (:ex:Org) 1 statement via negative_property_assertion
```

## ex:Org

```text
(:ex:Org) 1
  -ex:legacy-> xsd:string =old
```
