{#- glossary-<slug>.md: `view.graph` is a PatternGraph; the entries that have a line, as a list. -#}
# Glossary of {{ view.graph.graph_label }}

{% for entry in view.graph.glossary | selectattr("line") -%}
- {{ entry.line }}
{% else -%}
No term of this graph has a label or a description.
{% endfor -%}
