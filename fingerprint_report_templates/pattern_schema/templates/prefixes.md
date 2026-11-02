{#- prefixes-<slug>.md: `view.graph` is a PatternGraph; one row per prefix the graph's pattern view writes. -#}
# Prefixes of {{ view.graph.graph_label }}

| prefix | namespace | classes | properties | instances | triples |
|---|---|---:|---:|---:|---:|
{% for p in view.graph.prefixes -%}
| {{ p.prefix }} | <{{ p.namespace | replace("|", "\\|") }}> | {{ p.classes or 0 }} | {{ p.properties or 0 }} | {{ p.instances or 0 }} | {{ p.triples or 0 }} |
{% endfor -%}
