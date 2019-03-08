"""
  profile_ap
Created:  06/03/19
Author:   Eugeniu Costetchi
Email: costezki.eugen@gmail.com

    This module generates descriptive statistics based on the spo query below.
    The assumption is that the SPARQL query is executed at an endpoint and the
    result is available as an CSV file.

    The aim is to populate build a context object that can further be used to
    populate a document template.

    The work columns are:
        "stype",
        "p",
        "ootype",
        "propType",
        "scnt",
        "ocnt",
        "cnt",
        "min_sp",
        "max_sp",
        "avg_sp"

    SPARQL query:
    ---
    select distinct ?stype ?p ?ootype ?propType (count(distinct ?s) as ?scnt) (count(distinct ?o) as ?ocnt)
    (count(*) as ?cnt) (min(?sp_star) as ?min_sp) (max(?sp_star) as ?max_sp) (avg(?sp_star) as ?avg_sp)
    where
    {

      ?s ?p ?o .
      ?s a ?stype .
      optional {
        ?o a ?otype .
      }
      {
        select distinct ?s ?p (count(*)as ?sp_star)
                  {
                    ?s ?p [].
                  } group by ?s ?p
      }
      bind( if(?p=rdf:type, ?stype, if(bound(?otype),?otype, datatype(?o) )) as ?ootype )
      bind( if(?p=rdf:type,"object", if(bound(?otype),"object","data")) as ?propType)
    }
    group by ?stype ?p ?ootype ?propType
    order by ?stype ?p ?ootype ?propType
    ---
"""

# TODO put here the code that generated the content dictionary for the JINJA template

#