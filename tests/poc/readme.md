# fingerprint questions


## partition of the instantiated classes

how many instances are available for each class

# triple shapes

# Class shapes

```sparql
SELECT DISTINCT (?p as ?property) (?tto as ?object_type) (?tp as ?property_type)  				
				(count(distinct ?s) as ?scnt)
                (count(distinct ?o) as ?ocnt)
                (count(*) as ?cnt)
                (min(?sp_star) as ?min_sp)
                (max(?sp_star) as ?max_sp)
                (avg(?sp_star) as ?avg_sp)
WHERE
{
  values ?ts {<http://www.w3.org/2004/02/skos/core#Concept>}
  ?s a ?ts .
  ?s ?p ?o .
  OPTIONAL {?o a ?to .}
  BIND( datatype(?o) as ?dto )
  BIND(IF(BOUND(?to),?to, IF (bound(?dto), ?dto, <http://www.w3.org/2000/01/rdf-schema#Resource>) ) as ?tto )
  BIND( IF( isURI(?o),'object' , 'data') as ?tp )
  {
    select distinct ?s ?p (count(*)as ?sp_star)
    {
      ?s ?p [].
    } group by ?s ?p
  }
} GROUP BY ?ts ?p ?tto ?tp
ORDER BY ?subject_type desc(?property_type) desc(?count) ?property ?object_type
```

# namespaces 