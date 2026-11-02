# Patterns of default graph

Prefixes: `prefixes-default.md` · glossary: `glossary-default.md`

Legend: (:A&B) n: classes with the same n instances · ~m first_n: statistics over the first m read · co C k: k also typed C · via (:S)-p: incoming links · -p-> (:T|U) object classes · IRI, BNODE untyped · . not collected · deeper indent: a blank node's own edges, statistics over all its instances, up to 3 hops · ^ expanded under another edge · … deeper than 3 hops · k/n instances having p (omitted: all) · ×a-b values per instance (omitted: 1) · bn blank nodes · @n languages, @tag one language · =v one value · lo..hi range · dN distinct values (omitted: all differ) · presence found, not measured

## euvoc:Continent&skos:Concept

```text
(:euvoc:Continent&skos:Concept) 6
  -dcterms:created-> xsd:date =2014-10-10
  -euvoc:startDate-> xsd:date =1952-07-24
  -euvoc:status-> IRI d1
  -euvoc:xlNotation-> (:euvoc:XlNotation) bn
    -dcterms:created-> xsd:date =2014-10-10
    -dcterms:type-> IRI d1
    -euvoc:startDate-> xsd:date =1952-07-24
    -euvoc:status-> IRI d1
    -rdf:value-> xsd:string AFRICA..OCEANIA
  -skos:inScheme-> (:owl:Ontology&skos:ConceptScheme) d1
  -skos:topConceptOf-> (:owl:Ontology&skos:ConceptScheme) d1
  -skosxl:prefLabel-> (:skosxl:Label) ×24 bn
    -dcterms:created-> xsd:date =2014-10-10
    -dcterms:type-> IRI d1
    -euvoc:startDate-> xsd:date 1952-07-24..2014-10-10 d2
    -euvoc:status-> IRI d1
    -lvont:script-> IRI 12/145 d2
    -skosxl:literalForm-> rdf:langString @24
```

## owl:Ontology&skos:ConceptScheme

```text
(:owl:Ontology&skos:ConceptScheme) 1 via (:euvoc:Continent&skos:Concept)-skos:inScheme, (:euvoc:Continent&skos:Concept)-skos:topConceptOf
  -dcterms:created-> xsd:date =2014-10-10
  -dcterms:identifier-> xsd:string =http://publications.europa.eu/resource/authority/continent
  -euvoc:startDate-> xsd:date =2014-10-10
  -euvoc:status-> IRI
  -owl:imports-> IRI
  -rdfs:comment-> rdfs:Literal =Continent
  -skosxl:prefLabel-> (:skosxl:Label) bn ^
```
