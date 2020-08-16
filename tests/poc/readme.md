# fingerprint questions


## partition of the instantiated classes

how many instances are available for each class




# triples shapes

subject type | predicate | object type  | property type | occurences

```sparql
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
SELECT DISTINCT (?ts as ?subject_type)  (?p as ?property) (?tto as ?object_type) (?tp as ?property_type) ?count
WHERE 
{
  values ?ts {<http://publications.europa.eu/ontology/euvoc#Continent>}
  ?s a ?ts .
  ?s ?p [] .  
  {
    select ?ts ?p ?tto ?tp (count(*) AS ?count)
    {
      ?s ?p ?o .
      ?s a ?ts .
      OPTIONAL {?o a ?to .}
      BIND( datatype(?o) as ?dto )
      BIND(IF(BOUND(?to),?to, IF (bound(?dto), ?dto, <http://www.w3.org/2000/01/rdf-schema#Resource>) ) as ?tto )
      BIND( IF( isURI(?o),"object" , "data") as ?tp )
    } GROUP BY ?ts ?p ?tto ?tp
  }
}
ORDER BY ?ts ?p ?tto ?tp
```

## class shapes

unique properties

 