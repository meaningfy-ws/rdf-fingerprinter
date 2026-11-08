> Derives from: EPIC consumer-api-gaps (`proposal.md`); design C-1 to C-4.

## 1. Bounded endpoint calls (#76)

- [x] 1.1 Scenarios "A slow answer times out at the deadline" and "An oversized answer is refused" in `tests/features/fingerprint_report.feature` with steps (red)
- [x] 1.2 C-1 in `fingerprint/adapters/sparql.py`, `FingerprintConfig.max_answer_bytes`, `AnswerTooLarge`; green
- [x] 1.3 Docs: how-it-works, operational variables, worst case

## 2. Listing error contract (#77)

- [x] 2.1 Scenarios "A listing answer without the graph column is refused" and "A bad setting is not a bad URL" with steps (red)
- [x] 2.2 C-2; green
- [x] 2.3 API reference

## 3. Diagram descriptions (#75)

- [x] 3.1 Scenarios "Each diagram file is described" and "A split module has its part number" with steps (red)
- [x] 3.2 C-3 and `make generate-models`; green
- [x] 3.3 API reference and representations page

## 4. Formats reference (#69)

- [x] 4.1 Scenario "The API reference names every format" with step (red)
- [x] 4.2 C-4; green

## 5. Gates

- [x] 5.1 `make check-all` green; `CHANGELOG.md` Unreleased entry
