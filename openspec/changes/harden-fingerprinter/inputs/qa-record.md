# Q&A record — shaping harden-fingerprinter (2026-10-31, secondary, never groomed)

Developer answers, in conversation order.

1. Open an EPIC for the exploration; harden the library first.
2. Do not delete anything from the repo; record the cleanup candidates only.
3. Fetch comparable tools into sibling folders and compare methods and popularity → `prior-art.md`.
4. Focus on statistics collection first. It must work on large KGs, so a single global aggregate
   (option B) is likely unfeasible. Take void-generator's ideas, QSE/sheXer confidence and
   cardinality votes; capping heavy subqueries is acceptable.
5. "First N" (LIMIT without ORDER BY) is fine for capped samples.
6. Keep and apply eds4jinja2 (as the renderer). Representations go to a second EPIC
   (`profile-representations`). The statistics need a clear schema (LinkML). Implementation adopts
   cosmic-python / onion architecture and all Meaningfy best practices.
7. `llm-schema-tools` is a separate need — ignore it here.
8. Object types (Q7) may be looked up across graphs. The completeness check (Q10) is a
   configuration property or environment variable.
9. Precision is the goal; sampling is an optimisation. Keep all three modes (exact, batched,
   first_n); decide the trade-offs explicitly. Add literal lengths, languages, datatypes and value
   diversity. One algorithm or parallel implementations? → one algorithm (DEC-10).
10. Record every statistic from today's templates and the other tools in the LinkML model; two
    models: raw stats, and an analytical extension with computed values.
11. Namespace `fp: https://data.meaningfy.ws/fingerprint/` is fine; go ahead.
12. Appetite LARGE, hierarchy profiling in. Benchmark on a local dump in Oxigraph (then moved out, see 13). Always profile
    the default graph (today's behaviour). Collection defaults accepted: timeout 60 s, concurrency
    4, batch 2 000, first_n 10 000, distinct_limit 1 000 000, top_k 20, threshold 0.95, depth
    `values`, policy `auto`, object types `same_graph`, completeness check off.
13. Benchmarking moves to its own EPIC pitch (`benchmark-fingerprinter`).
14. Separate implementations per mode? No — one algorithm. Batched mode carries most of the complexity → moved to a follow-up EPIC (`batched-collection`, DEC-14 re-shape).
