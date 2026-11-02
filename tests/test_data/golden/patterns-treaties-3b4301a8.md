# Patterns of http://publications.europa.eu/resources/authority/treaties

Prefixes: `prefixes-treaties-3b4301a8.md` · glossary: `glossary-treaties-3b4301a8.md`

Legend: (:A&B) n: classes with the same n instances · ~m first_n: statistics over the first m read · co C k: k also typed C · via (:S)-p: incoming links · -p-> (:T|U) object classes · IRI, BNODE untyped · . not collected · deeper indent: a blank node's own edges, statistics over all its instances, up to 3 hops · ^ expanded under another edge · … deeper than 3 hops · k/n instances having p (omitted: all) · ×a-b values per instance (omitted: 1) · bn blank nodes · @n languages, @tag one language · =v one value · lo..hi range · dN distinct values (omitted: all differ) · presence found, not measured

## euvoc:Treaty&skos:Concept

```text
(:euvoc:Treaty&skos:Concept) 104 via (:euvoc:Treaty&skos:Concept)-dcterms:isReplacedBy, (:euvoc:Treaty&skos:Concept)-dcterms:replaces
  -dcterms:created-> xsd:date 2011-05-19..2018-05-17 d10
  -dcterms:dateAccepted-> xsd:date 2012-06-27..2018-06-06 d8
  -dcterms:dateSubmitted-> xsd:date 2011-10-06..2018-05-23 d8
  -dcterms:isReplacedBy-> (:euvoc:Treaty&skos:Concept) 22/104
  -dcterms:replaces-> (:euvoc:Treaty&skos:Concept) 22/104
  -dcterms:type-> IRI d6
  -eli:date_document-> xsd:date 83/104 1951-04-18..2012-02-02 d30
  -eli:first_date_entry_in_force-> xsd:date 82/104 1952-07-23..2013-07-01 d27
  -euvoc:endDate-> xsd:date 22/104 1951-01-01..2016-06-06 d13
  -euvoc:officialJournalDate-> xsd:date 92/104 1964-10-01..2016-06-07 d31
  -euvoc:officialJournalNumber-> xsd:string 92/104 1..91 d32
  -euvoc:officialJournalSeries-> xsd:string 92/104 C..P d3
  -euvoc:signatureLocation-> IRI 74/104 ×1-2 d13
  -euvoc:startDate-> xsd:date 1950-12-31..2016-06-07 d39
  -euvoc:status-> IRI d3
  -euvoc:xlChangeNote-> (:euvoc:XlNote) 1/104 bn ^
  -euvoc:xlDefinition-> (:euvoc:XlNote) 6/104 ×1-2 bn
    -dcterms:created-> xsd:date 2014-10-20..2018-05-17 d3
    -dcterms:source-> rdf:langString 10/12 @2 d3
    -euvoc:startDate-> xsd:date 1951-04-18..1993-03-25 d6
    -euvoc:status-> IRI d2
    -rdf:value-> rdf:langString @2
  -euvoc:xlHistoryNote-> (:euvoc:XlNote) 1/104 bn ^
  -euvoc:xlNotation-> (:euvoc:XlNotation) ×1-6 bn
    -dcterms:created-> xsd:date 157/357 2011-05-19..2018-05-17 d10
    -dcterms:type-> IRI d5
    -euvoc:endDate-> xsd:date 56/357 1951-01-01..2016-06-06 d13
    -euvoc:startDate-> xsd:date 157/357 1950-12-31..2016-06-07 d39
    -euvoc:status-> IRI 157/357 d3
    -rdf:value-> xsd:string 11951K..UNION d317
  -lemon:context-> IRI ×1-2 d2
  -skos:inScheme-> (:owl:Ontology&skos:ConceptScheme) d1
  -skos:topConceptOf-> (:owl:Ontology&skos:ConceptScheme) d1
  -skosxl:altLabel-> (:skosxl:Label) 56/104 ×1-74 bn ^
  -skosxl:prefLabel-> (:skosxl:Label) ×23-24 bn
    -dcterms:created-> xsd:date 4080/4530 2011-05-19..2018-05-17 d11
    -dcterms:type-> IRI d5
    -euvoc:endDate-> xsd:date 1216/4530 1951-01-01..2016-06-06 d13
    -euvoc:startDate-> xsd:date 4080/4530 1950-12-31..2016-06-07 d40
    -euvoc:status-> IRI d3
    -lvont:script-> IRI 386/4530 d2
    -skosxl:literalForm-> rdf:langString @24 d4176
```

## owl:Ontology&skos:ConceptScheme

```text
(:owl:Ontology&skos:ConceptScheme) 1 via (:euvoc:Treaty&skos:Concept)-skos:inScheme, (:euvoc:Treaty&skos:Concept)-skos:topConceptOf
  -dcterms:created-> xsd:date =2011-09-23
  -dcterms:identifier-> xsd:string =http://publications.europa.eu/resource/authority/treaty
  -euvoc:startDate-> xsd:date =2011-09-23
  -euvoc:status-> IRI
  -owl:imports-> IRI ×2
  -rdfs:comment-> rdfs:Literal =Treaty
  -skosxl:prefLabel-> (:skosxl:Label) bn ^
```
