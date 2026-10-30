<!-- The EPIC. In Meaningfy the EPIC *is* the OpenSpec proposal.
     The shaping sections (Appetite to No-gos) state the problem, the approach chosen and its limits;
     the sections after the rule (What Changes, Capabilities, Impact) feed the specs.

     What belongs here: WHY and WHAT, never HOW (that is design.md). Frozen once shaped; leave the
     implementer room.
     Decisions are declared HERE once, as DEC-n; design.md and tasks.md cite them, never restate them.
     General engineering rules live in their own skills; cite them, do not repeat them. -->

# EPIC: <short title>

## Appetite

<!-- One size: TINY / SMALL / MEDIUM / LARGE / VERY LARGE / HUGE — how deep and how extensive the
     solution may be (definitions in the epic-planning skill). Never days or weeks; not an estimate. -->

## Why

<!-- 1-2 sentences: the raw problem or opportunity. Why now? (The heading stays `## Why`, as OpenSpec expects.) -->

## Solution outline

<!-- The approach chosen, in enough detail to start, not the full design.
     State outcomes (the problem solved / the metric moved), not a list of buttons or features. -->

## Key decisions

<!-- Decisions already taken, each with its reason and the alternative rejected. Give each an id
     (DEC-1, …) so the design, tasks and specs can cite it. -->
- **DEC-1**: <decision> — <reason>; rejected: <alternative>

## Rabbit-holes

<!-- Known traps to avoid; things deliberately left vague. -->

## No-gos

<!-- MANDATORY. Explicitly out of scope. An EPIC without no-gos is not ready to plan. -->

---

## What Changes

<!-- Bullet list of concrete changes. Mark breaking changes **BREAKING**. -->

## Capabilities

### New Capabilities
<!-- kebab-case names; each becomes specs/<name>/spec.md -->
- `<name>`: <what this capability covers>

### Modified Capabilities
<!-- Existing specs whose REQUIREMENTS change. Check openspec/specs/ first. Leave empty if none. -->

## Impact

<!-- Affected code, APIs, dependencies, systems. -->
