<!-- PLAN (design half). PLAN = this file + tasks.md. The clarity gate scores the pair (≥9/10).

     What belongs here: HOW, and why this how. Cite the EPIC's DEC-n; never re-explain a settled decision.
     Acceptance criteria live in the spec deltas as WHEN/THEN scenarios, NOT here. -->

> Derives from: <the EPIC this plan derives from>

## Context

<!-- Background, current state, constraints. -->

## Goals / Non-Goals

**Goals:**

**Non-Goals:**

## Decisions

<!-- NEW technical choices made while planning + rationale (why X over Y; alternatives considered).
     For anything already settled in the EPIC, cite its DEC-n — do not re-explain it. -->

## Algorithm / approach

<!-- The shape of the solution; concrete worked examples.
     Idempotency by design: state whether operations are safe to retry/replay (at-least-once) and how
     (idempotency keys, upserts, dedupe) — or why the operation is inherently safe. -->

### Anti-patterns
<!-- Explicit things to avoid in this change. -->
| Don't | Do instead | Why |
|---|---|---|

## Error matrix

<!-- Failure mode → how it is detected → expected handling. Include retry/replay paths (timeouts, duplicate delivery) and
     the idempotency guarantee that keeps them safe. -->
| Failure mode | How it is detected | Expected handling |
|---|---|---|

## Risks / Trade-offs

<!-- [Risk] → Mitigation -->

## Open Questions

<!-- Unknowns to resolve. HARD questions get parked here, not guessed. -->
