# pitfall-scans — delta for singleton-property-pattern

## MODIFIED Requirements

### Requirement: The packaged catalogue
The fingerprinter SHALL ship a catalogue of checks covering these OOPS! pitfalls: P04, P05, P06, P07, P08,
P10, P11, P12/P30 (by local name), P13, P19, P20, P21, P22, P24 (direct cases), P25, P26, P27,
P28/P29, P32, P33, P34, P35, P36, P38 and P41. It SHALL also ship three checks beyond OOPS!: an IRI
used as a class and as a property, subjects outside a property's declared domain, and IRI objects
outside an object property's declared range. It SHALL NOT ship a check for typed individuals used as
predicates: those are reifications, reported as reified relations (statistics-collection "Reified
relations are grouped by what they stand for"; singleton-property-pattern DEC-10). Each check's
`source` SHALL name its OOPS! pitfall code where it has one, and its title and description SHALL be
the fingerprinter's own words (EPIC DEC-12). The catalogue's ids, importance, scope and heuristic
flags SHALL be those of design.md's catalogue table, without `x_individual_as_predicate`.

#### Scenario: Catalogue size
- **WHEN** the packaged catalogue is loaded
- **THEN** it holds 28 checks, each with a unique id, none of them `x_individual_as_predicate`, and every OOPS!-derived check's source names its pitfall code

#### Scenario Outline: Each check finds its pitfall and only it
- **WHEN** check <id> runs over its positive fixture and over its negative fixture
- **THEN** it finds at least one row in the positive fixture, the expected entity among them, and no row in the negative fixture

  Examples:
    | id                                   |
    | every packaged check (one row each)  |
