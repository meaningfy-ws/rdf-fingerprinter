# profile-representations — delta for singleton-property-pattern

## ADDED Requirements

### Requirement: Reified relations per class
Every descriptive output that lists properties per class (profile document, pattern view and schema,
PlantUML diagram) SHALL show the class's reified relations in a separate section after its
properties, each with kind, generic predicate (or "unnamed"), object class, statement count and
reifier properties. A class with none SHALL show no section. SHACL and ShExC outputs SHALL note
each reified relation under the class's shape (an annotation in SHACL, a comment in ShExC) and SHALL
NOT constrain it.

#### Scenario: Section present
- **GIVEN** a profile where class A has a reified relation `ex:isRelatedTo` to B
- **WHEN** the profile document is generated
- **THEN** A's entry has a reified-relations section naming `ex:isRelatedTo`, B and the count

#### Scenario: No section when none
- **GIVEN** a profile with no reified relations
- **WHEN** any output is generated
- **THEN** it equals the output for the same profile before this change

#### Scenario: Shapes note reifications without constraining them
- **GIVEN** a profile where class A has a reified relation `ex:isRelatedTo` to B
- **WHEN** SHACL shapes and ShExC are generated
- **THEN** A's shape notes `ex:isRelatedTo` to B, and has no property shape or triple constraint for
  the relation or its reifier properties
