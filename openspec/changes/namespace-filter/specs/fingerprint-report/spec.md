## MODIFIED Requirements

### Requirement: Navigation, search and filters
The report SHALL have:
- a table of contents by graph, namespace and class, linking to each class section;
- a search box, matching case-insensitive substrings of short names and full IRIs. A class whose own
  name matches stays shown with all its rows. A class where only some property rows match stays
  shown with just those rows. Any other class is hidden. An empty query shows everything;
- one switch per prefix of a shown class or a shown property, in prefix order. Switching one off
  SHALL hide that namespace's class sections and its property rows in every class section
  (namespace-filter DEC-10);
- the counts of shown and hidden classes, always visible, reflecting the search and switches (the
  classes left out by the filters are listed in the caveats).

Search and switches SHALL combine: a class is shown only when its switch is on and the search
allows it, and a property row is shown only when its switch is on and the search allows it; a class
shown because some of its rows match needs one such row whose switch is on. Class sections SHALL be
collapsible without JavaScript. Every class section SHALL carry its namespace prefix and its
searchable text as data attributes, and every property row its property's prefix (empty when no
prefix covers the property). The scripted behaviour SHALL be checked by hand once per change
(namespace-filter DEC-10; readable-representations DEC-4).

#### Scenario: Search data is present
- **WHEN** the report is generated for the readability test profile
- **THEN** each class section carries its prefix and a searchable text holding its short name and full IRI

#### Scenario: Property rows carry their prefix
- **WHEN** the report is generated for the filter test profile with no filter option
- **THEN** each property row carries its property's prefix, and there is one switch for each of `ex`, `org`, `rdfs` and `rel`, though no class is in `rdfs` or `rel`

#### Scenario: Search narrows the classes
- **WHEN** the reader types `risk` in the search box of the brainframe report (checked by hand)
- **THEN** only the classes and property rows whose names or IRIs contain `risk` stay shown, and the shown count updates

#### Scenario: Namespace switched off
- **WHEN** the reader switches off a namespace
- **THEN** its class sections and table of contents entries are hidden, and the search still applies to the rest

#### Scenario: Property namespace switched off
- **WHEN** the reader switches off `relationid` in the brainframe report generated with no filter option (checked by hand)
- **THEN** every `relationid:` property row is hidden, every class section stays, and the search still applies to the rows left

#### Scenario: Search and a property switch combine
- **WHEN** the reader of the brainframe report generated with no filter option types `2822a123`, then switches off `relationid` (checked by hand)
- **THEN** the search first shows `brainframe:CloudInfrastructure` alone, the one class with a matching row, a `relationid:` row; with the switch off that class is hidden too, and the count goes from `1 shown, <T−1> hidden` to `0 shown, <T> hidden`, where `<T>` is the number of class sections
