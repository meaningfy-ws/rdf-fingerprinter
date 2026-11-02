# Research notes — teaching LLMs a graph schema for query generation — 2026-10-31 (seed input, not groomed)

Question: how do you tell an LLM what a graph's schema is so it writes correct SPARQL, Cypher or
Gremlin, and what do studies say works? Desk research from web searches; papers were read at
abstract level unless noted. Written while shaping `harden-fingerprinter` (its Q4); moved here
as the seed of this EPIC.

## The methods, as the literature groups them

1. **Put the schema in the prompt (static).** Serialise the whole schema once and prepend it:
   an OWL/RDFS ontology in Turtle, a list of classes and properties, ShEx/SHACL shapes, Cypher
   `(:Label)-[:REL]->(:Label)` patterns, Gremlin vertex/edge/property lists. This is the baseline
   that every study starts from. It breaks down when the schema exceeds the context window or
   floods it with irrelevant detail.
2. **Prune the schema per question (dynamic / schema linking).** Retrieve only the classes,
   properties and relations relevant to the question (embedding search, string match, or an
   LLM selection step), then prompt with that slice. This is the step text-to-SQL calls
   schema linking.
3. **Enrich the schema with data-derived facts.** Add what the ontology alone does not say:
   which predicates a class *actually* uses, domain/range as observed, value types, cardinality,
   sample values, counts, `rdfs:label`/`rdfs:comment`. Neo4j's "enhanced schema" (property value
   samples and ranges) and VoID-derived shapes are both this idea.
4. **Retrieve example queries (few-shot).** Index question/query pairs for the target graph and
   put the nearest ones in the prompt. They teach both the schema and the house idiom.
5. **Validate and repair against the schema.** Parse the generated query, check its classes,
   predicates and domain/range against the schema, run it, and feed errors or empty results
   back for a retry.
6. **Agentic exploration.** Give the LLM tools (list classes, describe class, probe predicates,
   run query) and let it discover the schema on the endpoint step by step (ReAct style).
7. **Fine-tune.** Train a small model on question/query pairs for one graph or one language.
   This is strong in-domain and brittle when the schema changes.

## Studies and what they found

### SPARQL / RDF

- **Sequeda, Allemang, Jacob (2023), "A Benchmark to Understand the Role of Knowledge Graphs on
  LLM's Accuracy for Question Answering on Enterprise SQL Databases"** (arXiv 2311.07509).
  On an insurance schema, GPT-4 zero-shot scored 16.7% over SQL and 54.2% over the same data as
  an ontology-backed KG queried with SPARQL. All tested questions with high schema complexity
  failed on SQL. Caveats: the authors were at data.world, a KG vendor, and the study covers one
  domain.
- **Allemang & Sequeda (2024), "Increasing the LLM Accuracy for Question Answering: Ontologies to
  the Rescue!"** (arXiv 2405.11706). An ontology-based query check (OBQC) validates the
  generated SPARQL against domain/range and other ontology rules, and an LLM repairs the
  failures. Accuracy rose to about 72%, with a further ~8% answered "I don't know". This is
  method 5.
- **Emonet et al. (2024), "LLM-based SPARQL Query Generation from Natural Language over Federated
  Knowledge Graphs"** (arXiv 2410.06062, SIB/Expasy) and **Smeros et al. (2025/26),
  "SPARQL-LLM"** (arXiv 2512.14277, `pip install sparql-llm`). They read each endpoint's **VoID
  class/property partitions**, turn them into per-class **ShEx shapes** (each class's predicates
  and their target classes/datatypes), index the shapes together with example queries, retrieve
  per question, and validate the generated query against the shapes. They chose ShEx over OWL
  because its syntax is closer to SPARQL. They also note that a schema derived from the endpoint's
  real content beats a generic ontology. SPARQL-LLM reports first place at TEXT2SPARQL 2026, up
  to 59% higher F1 than the runner-up, at ≤ $0.01 per question. *(VoID→ShEx details come from
  search excerpts; not checked in the full text.)*
- **Rasheed & Aguado (2025), Knowledge Organization 52(8)**, ERA railway ontology (RINF).
  They compared a plain list of classes/properties/instances with a reduced ontology in Turtle
  (detailed and short prompts) on 20 questions. Gemini scored 85% with the list, 85% with short
  Turtle and 75% with detailed Turtle; GPT-3.5 scored 50% with every format. The bare vocabulary
  list was as good as Turtle at a fraction of the tokens.
- **Fitch & Kurtz (2026), "Natural Language Access to Domain-Specific Metadata"** (arXiv
  2607.18029). Ablation over eight ontology representations: **readable entity names and
  semantic annotations (labels/comments) mattered more than model choice or prompt
  engineering**. OWL beat SQL DDL as schema context. Per-format numbers are not on the
  abstract page.
- **D'Abramo et al. (2025), "Investigating LLMs for Text-to-SPARQL Generation"** (KnowledgeNLP @
  ACL 2025). Retrieved few-shot demonstrations plus several candidate queries reached
  state-of-the-art results on several KGQA benchmarks without fine-tuning (method 4).
- **FIRESPARQL** (arXiv 2508.10467). On scholarly KGs, errors split into structural (missing
  or extra triple patterns) and semantic (wrong entity or property). The authors trace both
  to the model seeing too little schema. The fix: fine-tuning plus RAG over the schema.
- **SAGA** (arXiv 2607.14494) and **AutoSchema** (arXiv 2608.14228). Both argue the schema should
  *constrain generation* — types tracked per variable, predicates that conflict with the domain
  filtered out — and not only sit in the prompt or check the query afterwards. AutoSchema fetches
  the schema live from the endpoint.
- **TEXT2SPARQL challenge** (ESWC 2025, CEUR Vol-4094; 2026 edition). The 2025 edition ran on
  DBpedia plus a small corporate KG. Strong 2025 entries combined predicate/entity linking
  against the KG with few-shot prompts (AIRI) or a ReAct agent exploring the graph
  (ARUQULA, arXiv 2510.02200).

### Cypher / property graphs

- **Ozsoy (2025), "Enhancing Text2Cypher with Schema Filtering"** (arXiv 2505.05118, Neo4j;
  LLM-TEXT2KG @ ESWC 2025). Compared two static full-schema formats with three dynamic,
  per-question pruning methods. **Pruning helps small models most**. Large models gain less
  accuracy but still save tokens. **Pruning too much drops needed elements and lowers
  accuracy.** Neo4j's blog version reports that the full schema made prompts over 2,700 tokens
  against ~150 for the instructions, and a base schema cut p95 prompt length to about a third.
- **Ozsoy et al. (2025), "Text2Cypher: Bridging Natural Language and Graph Databases"**
  (GenAIK @ COLING 2025). Released a public Text2Cypher dataset of about 44k pairs. Large
  foundation models scored best, and fine-tuned small models were competitive.
- **Text2GraphQuery-Bench** (arXiv 2602.11745, 2026). Covers Cypher, GQL and SQL/PGQ. Abstract
  questions hurt most, because intent is hard to ground in the schema. Renaming schema elements
  (aliasing) barely matters. Few-shot examples close most of the gap between Cypher and the
  less-known languages.

### Gremlin

- No peer-reviewed text-to-Gremlin study on schema representation turned up. The closest is an
  **AWS engineering blog (2025)** for Neptune/Bedrock. It extracts vertex and edge types and
  their properties into a text-to-SQL-style schema, adds domain notes (e.g. "metadata vertices,
  never query"), and repairs failed queries by sending the error back to the LLM. It reports 74%
  on 120 questions, judged by an LLM.
- **LDBC Text2GQ task force** (charter v0.1.2) is building a cross-language benchmark with
  schemas in GQL graph types / PG-Schema; baselines are planned for 2026.
- Gremlin is imperative (traversal steps), so models have seen less of it. The same schema
  techniques apply, but expect few-shot examples and error feedback to matter more.

## Takeaways

- **The schema the model gets matters more than which model it is.** Readable names, labels
  and comments, and a compact form beat a full ontology dump.
- **Data-derived schema beats declared schema.** What the endpoint *actually* contains — classes,
  the predicates each class uses, target types, cardinality — grounds queries better than an
  OWL file that may not match the data.
- **Compact over complete; prune per question, but not too hard.**
- **Shape-style per-class descriptions (ShEx/SHACL-like) are the leading SPARQL format**, because
  they read like the triple patterns the model must write.
- **Few-shot retrieval and a validate-and-repair loop are the cheapest large gains** in every
  language.
- **Agents that explore the live endpoint** are the current frontier for large or unfamiliar KGs.

## Relevance to this EPIC

The fingerprint report already computes, per graph and class, the properties instances use,
with counts, min/max/avg cardinality, property kind and object/value types. That is nearly the
data-derived per-class shape that SPARQL-LLM builds from VoID before prompting. Emitting VoID
and compact shapes, and serving them over MCP, would make the fingerprinter a lightweight
producer for text-to-SPARQL pipelines, the role `sib-swiss/void-generator` plays today for
`sparql-llm`.

## Sources

- https://arxiv.org/abs/2311.07509 — Sequeda et al. 2023, KG benchmark
- https://arxiv.org/abs/2405.11706 — Allemang & Sequeda 2024, ontology-based query check
- https://arxiv.org/abs/2410.06062 — Emonet et al. 2024, federated SPARQL generation (VoID→ShEx)
- https://arxiv.org/abs/2512.14277 — SPARQL-LLM; https://pypi.org/project/sparql-llm/
- https://www.imrpress.com/journal/KO/52/8/10.31083/KO42705 — Rasheed & Aguado 2025
- https://arxiv.org/abs/2607.18029 — Fitch & Kurtz 2026, ontology representation ablation
- https://aclanthology.org/2025.knowledgenlp-1.5.pdf — D'Abramo et al. 2025
- https://arxiv.org/abs/2508.10467 — FIRESPARQL
- https://arxiv.org/abs/2607.14494 — SAGA; https://arxiv.org/abs/2608.14228 — AutoSchema
- https://ceur-ws.org/Vol-4094/ — TEXT2SPARQL 2025 proceedings; https://arxiv.org/abs/2510.02200 — ARUQULA
- https://arxiv.org/abs/2505.05118 — Ozsoy 2025, Text2Cypher schema filtering
- https://neo4j.com/blog/developer/schema-representation-in-text2cypher/ — Neo4j blog
- https://aclanthology.org/2025.genaik-1.11.pdf — Text2Cypher dataset paper
- https://arxiv.org/abs/2602.11745 — Text2GraphQuery-Bench
- https://aws.amazon.com/blogs/machine-learning/generate-gremlin-queries-using-amazon-bedrock-models — AWS Gremlin blog
- https://ldbcouncil.org/docs/papers/text2gq-work-charter-v0.1.2.pdf — LDBC Text2GQ charter
