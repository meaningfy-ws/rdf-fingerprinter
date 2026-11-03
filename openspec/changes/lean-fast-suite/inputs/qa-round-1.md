# Q&A round 1 — lean-fast-suite (2026-11-02)

Secondary input, preserved as captured. Answers by the developer.

1. **Base branch for the worktree?** develop lacks the check-all-fast / check-all-deep split (on
   `feature/llm-schema-split`, PR #50, open).
   → **Start from `feature/llm-schema-split` HEAD** (010d943); retarget the PR to `develop` once
   #50 merges.
2. **What proves a deleted service-layer unit test may stay deleted?**
   → **Coverage + killed mutants, per module**: delete a module's batch of candidates; keep the
   deletions only when branch coverage and the killed-mutant set are unchanged; one mutmut run per
   module, not per test. (Rejected: coverage per deletion + final score only; strict P-6 per test.)
3. **The 9-case unit copy of "Shapes report no violation on their own data"?**
   → **Move the threshold matrix to the deep gate** behind a marker; the BDD scenario stays in the
   fast gate. (Rejected: delete the unit copy.)
4. **pytest-xdist?**
   → **In scope**, for both gates. (Rejected: keep the suite serial.)

## Round 2

5. **Fast-gate time budget?** → **No number; just lower** (report before and after).
6. **Does `make test-fast` keep reporting coverage?** The developer, verbatim:
   > optimise, do the best, we culd in fact allow ourselves to do more in the ci, if it is the
   > right thing to do, maybe no heavy infra with blazegraph and e2e otherwise we could do all of
   > them execept mutmut and e2e, what do you think?

   → Recommendation taken into the EPIC as DEC-5: local `make test-fast` without coverage; CI's
   PR check runs `make check-all-deep` (Hypothesis + coverage floors); e2e and mutmut stay out of
   the PR check. To confirm at the EPIC review.
7. **Plain unit tests for `fingerprint/domain/patterns.py`?** → **Yes, in scope** (DEC-6).

## Round 3 — how to group and run tests

8. **What do fast and deep mean, and are they still worth keeping?** The developer: "so i guess
   fast and deep makes no longer sense the split". Alternatives offered: by tier (A), by what a
   test needs (B), by cost (C), by capability (D), by change impact (E), by purpose (F), staged CI
   (G).
9. The developer, verbatim:
   > yes keep A, and have rules for default de tests to be run on every feature implementation,
   > and some otehr tests are run locally on when releasing, and the same CIs shall distingish some
   > for release and some for pr

   → Folders by tier (DEC-3); a feature gate (DEC-4) and a release gate, local (DEC-5) and CI
   (DEC-6). Earlier in the round: e2e before every release and Hypothesis run regularly locally
   (DEC-5, DEC-8).
10. **When does CI's release run fire?** → **On PRs into `master`.**
11. **What does CI's release run add?** Offered: e2e with an Oxigraph service, the mutation
    ratchet, a wheel build-and-install check. → **No answer recorded; open** (DEC-6 "to confirm").

## Round 4

12. **Release-only checks in CI?** The developer: "1. okay 2. mutmut not on release, after release
    eventually 3. yes okay — proceed with everything towards conclusion".
    → e2e against an Oxigraph service: yes. Wheel build-and-install check: yes. Mutation ratchet:
    not in the release check; after a release (on the published GitHub Release, and on demand).
    The weekly schedule is dropped in favour of the after-release trigger (agent's call, DEC-6).
