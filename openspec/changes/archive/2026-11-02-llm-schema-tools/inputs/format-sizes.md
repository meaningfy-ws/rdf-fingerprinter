# Format sizes on the sample data (task 1.12, DEC-8)

Unicode code points (`wc -m`) of the golden files in `tests/test_data/golden/`, measured on the
sample profile after `make refresh-golden`. "Without prefixes" drops the `PREFIX` lines; "body"
also drops the legend line. Re-measure after any change to the goldens.

| File | Full | Without prefixes | Body (no prefixes, no legend) |
|---|---:|---:|---:|
| `pattern-continents-214e8f67.txt` | 2287 | 1830 | 1234 |
| `pattern-default.txt` | 2287 | 1830 | 1234 |
| `pattern-treaties-3b4301a8.txt` | 3931 | 3378 | 2782 |
| `shex-continents-214e8f67.shex` | 2212 | 1755 | 1455 |
| `shex-default.shex` | 2212 | 1755 | 1455 |
| `shex-treaties-3b4301a8.shex` | 4113 | 3560 | 3260 |

The prefix block is 457 code points for `continents` and 553 for `treaties`; the pattern legend is
596 and the ShExC legend 300 in both. `pattern-default` and `shex-default` hold the same graph as
`continents` (the test data loads it into the default graph too), so they match byte for byte in size.

For reference, SHACL and the other formats of the same profile:

| File | Code points |
|---|---:|
| `shapes-continents-214e8f67.ttl` | 10950 |
| `shapes-default.ttl` | 10903 |
| `shapes-treaties-3b4301a8.ttl` | 23647 |
| `diagram-continents-214e8f67.puml` (overview) | 303 |
| `diagram-treaties-3b4301a8.puml` (overview) | 301 |
| `main.html` (report) | 127818 |

Reading: the pattern body of `continents` is about 9 times smaller than its SHACL (1234 vs 10950),
and the whole file with prefixes and legend is about 5 times smaller. The ShExC body is a little
larger than the pattern body (1455 vs 1234) because of the braces, `;` and `@` references.
Design section E expects "about 1,700 characters" for the `continents` pattern text without the
legend line; the measured 1830 (with prefixes) is 8% above that estimate.
