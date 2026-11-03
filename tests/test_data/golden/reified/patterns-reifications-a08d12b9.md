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

## ex:Actor

```text
(:ex:Actor) 1
```

## ex:Archive

```text
(:ex:Archive) 1
```

## ex:Building

```text
(:ex:Building) 1
  -ex:height-> BNODE bn
~> ex:height (:?) 1 statement via structured_value [reifiers: ex:unit 1]
```

## ex:Dataset

```text
(:ex:Dataset) 1
~> dcat:qualifiedRelation (:ex:Archive) 1 statement via dcat_qualified [reifiers: dcat:hadRole 1]
```

## ex:Entry

```text
(:ex:Entry) 1
  -ex:code-> (:ex:Notation)
```

## ex:Event

```text
(:ex:Event) 1
~> crm:PC14_carried_out_by (:ex:Actor) 1 statement via cidoc_property_of_property [reifiers: ex:note 1]
```

## ex:Firm

```text
(:ex:Firm) 1
```

## ex:Item

```text
(:ex:Item) 1
~> ex:claimP1 (:ex:Place) 1 statement via wikibase_statement [reifiers: ex:rank 1]
```

## ex:Notation

```text
(:ex:Notation) 1 via (:ex:Entry)-ex:code
  -rdf:value-> xsd:string =A1
```

## ex:Office

```text
(:ex:Office) 1
  -ex:address-> (:ex:Address) bn
    -ex:street-> xsd:string ="Main St"
```

## ex:Org

```text
(:ex:Org) 1
  -ex:legacy-> xsd:string =old
```

## ex:Place

```text
(:ex:Place) 1
```

## ex:Project

```text
(:ex:Project) 1
  -ex:role-> BNODE bn
~> ex:role (:?) 1 statement via blank_nary [reifiers: ex:agent 1, ex:since 1]
```

## ex:Run

```text
(:ex:Run) 1
~> prov:qualifiedAssociation (:ex:Team) 1 statement via prov_qualified [reifiers: prov:hadRole 1]
```

## ex:Team

```text
(:ex:Team) 1
```

## ex:Worker

```text
(:ex:Worker) 1
  -schema:affiliation-> (:schema:OrganizationRole)
~> schema:affiliation (:ex:Firm) 1 statement via schema_role [reifiers: schema:startDate 1]
```

## skos:Concept

```text
(:skos:Concept) 1
  -skosxl:prefLabel-> (:skosxl:Label)
```

## skosxl:Label

```text
(:skosxl:Label) 1 via (:skos:Concept)-skosxl:prefLabel
  -dcterms:source-> IRI
  -skosxl:literalForm-> rdf:langString @en
```
