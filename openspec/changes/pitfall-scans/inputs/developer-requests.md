# Seed: the developer's requests (2026-11-01)

This is a seed input, verbatim and never groomed. These requests came after the brainframe quality
run (`brainframe-robot-report.md`, `brainframe-modelling-analysis.md`, `seed-queries/`).

> can you lookup more oops querries? did you close the repo as a sibling repo?
> what would it take to extend the fingerprinte with such qualiy querries? to have a section with pitfalls?

> do you have any pitfall scanner checking for relations that have not been defined? (I was quite a few in brainframe data)

> once you finish the invetory of pitfalls, can you please write a new epic change that aims at extending the fingerprinter with pitfall scanns?
> then commit this epic, to anotehr branch (be careful, there is anotehr agent working here as well, so you might as well use worktrees to be safe);
> and then once you finihs the proposal, proceed with shaping the epc and checking the quality gates then commit and push to that branch
> please consder all the implications of extending the fingerptinging functionality at all the levels.

> I would say tahte you then go ahead and implement that epic on a separate worktree, wor independently towards completiion, do not merge, just commit and push. we will make corections to the testing strategy afterwards, a not it is being implemented on anotehr branch

## How the decisions were taken

The developer asked for independent work towards completion. So the agent took the shaping
decisions itself (EPIC DEC-1 to DEC-12), each with its reason and the alternative rejected, for the
developer to review on the branch. The developer said the testing strategy will be corrected
afterwards. Earlier context: the release authority and the conventions in `AGENTS.md`; the
`readable-representations` change (3.0.0) is the baseline.

## Report requests after the first brainframe scan (2026-11-01)

These requests came in after master's lean-test-suite merge.

> i noticed that in the main html the classes were not groupped, and were not ordered. also i saw there is no taxonomy view. would it be possible to add a taxonomy view, which also indicateas how popular a class is ?

> did you add a logic adnd capability  for similar sorting and groupping of properties per class?

The agent proposed this ordering: classes grouped by namespace, then by instance count descending;
properties grouped own, then refined, then inherited, and within each group by subjects descending,
then confidence, then short name. The SHACL, PlantUML and TSV outputs keep their IRI order. The
developer answered:

> yes, go ahead with that ordering

> the pitfalls section and caveats sections could be merged

> once you are done, update the epc specs with these latest requests

## 2026-11-01, after the regenerated brainframe report (verbatim)

On the doubled `brainframe-brainframe` prefix (the ontology IRI found by p10/p41 made `…/2016/04/`
a namespace, which took the short name), offered: 1. don't prefix the ontology's own IRI from
findings; 2. let the more-used namespace take the short name.

> go with 1.
> add also more ordering (in namespaces list, by popularity and grouping by source), add a small
> indicator also for each class, humber f instanes and number of distinct properties (two numbers
> data and object properties)
> update the spec as well , and work toward the concluding this epic
