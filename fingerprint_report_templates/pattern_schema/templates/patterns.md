{#- patterns-<slug>.md: `view.graph` is a PatternGraph. Header, edge text and the other lines come ready from
    fingerprint/domain/patterns.py; this template only lays them out. -#}
{% macro lines(edges) -%}
{% for edge in edges -%}
{{ "  " * edge.depth }}{{ edge.text }}
{{ lines(edge.edges) -}}
{% endfor -%}
{%- endmacro -%}
{% set g = view.graph -%}
# Patterns of {{ g.graph_label }}

Prefixes: `prefixes-{{ g.slug }}.md` · glossary: `glossary-{{ g.slug }}.md`

Legend: (:A&B) n: classes with the same n instances · ~m first_n: statistics over the first m read · co C k: k also typed C · via (:S)-p: incoming links · -p-> (:T|U) object classes · IRI, BNODE untyped · . not collected · deeper indent: a blank node's own edges, statistics over all its instances, up to 3 hops · ^ expanded under another edge · … deeper than 3 hops · k/n instances having p (omitted: all) · ×a-b values per instance (omitted: 1) · bn blank nodes · @n languages, @tag one language · =v one value · lo..hi range · dN distinct values (omitted: all differ) · presence found, not measured
{% if g.hidden_classes %}
Hidden: {{ g.hidden_classes }} classes.
{% endif -%}
{% if g.excluded_note %}
Excluded namespaces: {{ g.excluded_note }}.
{% endif -%}
{% for block in g.blocks %}
## {{ block.name }}

```text
{{ block.header }}
{{ lines(block.edges) -}}
{% for r in block.reified_relations or [] -%}
{{ r.text }}
{% endfor -%}
```
{% endfor -%}
