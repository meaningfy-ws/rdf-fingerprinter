## ADDED Requirements

### Requirement: Representations derive from the profile only
Every representation of a fingerprint (SHACL, PlantUML, ReSpec-style HTML, VoID, JSON/YAML) SHALL be
rendered from the analytics profile alone and SHALL NOT query the endpoint (EPIC DEC-1). Draft: the
full requirement set is written when this EPIC is shaped.

#### Scenario: Rendering without an endpoint
- **WHEN** a representation is rendered from a profile loaded from JSON with no endpoint reachable
- **THEN** the representation is written and no SPARQL request is made
