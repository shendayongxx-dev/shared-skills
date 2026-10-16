---
name: 02-consumer-agent-skill
description: Evaluate e-commerce posters using A-group complete briefs and C-group locked P-M-S tags. Return 0–100 scores, actionable feedback, unchanged eight-group protected content and regression locks.
license: MIT
metadata:
  author: xyu
  version: 1.5.3
  last_reviewed: 2026-10-05
---

# Consumer Agent: A-D-2.0 Interface

Evaluate once and output JSON only. A manages generation, hard compliance, logging, retries, and agent switches. C supplies classification assets and rules. Read `references/integration.md` for assembly and routing, and `assets/schemas/input.schema.json` and `output.schema.json` for the formal contract.

## Complete Input

`source_input` preserves A's complete normalized input and any additional original brief fields. `style_guide` preserves C's selected result. `protected_content` must be A's eight object groups, with `product_quantity` as an integer or `null`. `scripts/assemble_input.py` assembles `evaluation_context` deterministically. Explicit themes, additional display requirements, and brand character come from the original task; never infer product facts from cases or style.

`product_img` defaults to the first primary image, but inspect every relevant reference in `source_input.product.image_refs`. If the brand has no `logo_ref`, evaluate recognition of existing brand text only; do not require creation of a logo.

P-M-S order is fixed and the string `"null"` is accepted. Values must match `style_guide.tags` item by item. Evaluate an unknown dimension only from the known brief and tags: do not invent a class and do not automatically deduct or award full points. Record uncertainty. If a known tag conflicts materially with the brief, return `complete_input` so A/C can reconcile it; do not force a valid brief into a conflicting scenario.

## Scoring

First inspect the current image without the brief, then compare it with the complete input. Read `references/rubric.md`, `references/evaluation-lenses.md`, `references/subcriteria-anchors.md`, and `references/candidate-boundaries.md`.

There are five 20-point dimensions for a total of 100. The model must submit all 25 subcriteria defined in `assets/rubric.json`, each with an integer `level` from 0 through 4 and non-empty `evidence`. It must not directly fill `dimension_scores` or `dimension_evidence`; the deterministic aggregator computes both with decimal ROUND_HALF_UP. P sets communication requirements, M sets benefit-evidence priority, and S sets usage relationships; none changes dimension weights. Cases without complete human score annotations are expression references only.

For every level, apply adjacent-level boundaries. Case IDs are candidate expression references, not facts and not automatic scores. Determine D5 critical concerns from the task before viewing the image, record evidence after viewing, then compare the boundary. Do not award level 4 merely because the poster looks good when its enhancement condition is absent. If an important fact is missing from the input, return `complete_input` rather than a low level. The 1.5.1 boundary update begins a new scoring track and cannot be interpreted directly as poster improvement relative to the older scale.

Set `pass=true` only when total ≥80, every dimension ≥14, there is no `hard_fail`, and no locked dimension regressed. Model scoring is a simulated consumer judgment.

Explicit factual conflict, product/logo alteration, or missing required information is a `hard_fail` and must appear in `critical_issues`. A fact never supplied is an input problem.

## Actionable Feedback

Label residual suggestions after a pass as optional improvements; they do not trigger consumer redraw and routing continues according to `pass` and `next_route`. Label failed items as required for this round. Do not add output fields.

Pair `problem_list` and `modify_suggestion` one to one, with at most three priority problems. Every suggestion states `object/location; action; exact content; protected items; acceptance criteria`. Every failure needs an action; unresolved problems carry into the next round.

The aggregator deep-copies `protected_content` from input. D must not add, delete, merge, translate, or reorder its values. Fact locks and dimension locks are separate; asset position and ratio may be optimized within the brief.

`locked_dimensions` inherits earlier locks and adds dimensions reaching 14. Recheck all dimensions every round; record any old lock falling below 14 in `regressed_dimensions`. A hard fail adds no new lock but preserves old locks. Input errors preserve recoverable protected objects and old locks.

`context_hash` freezes the brief, C result, protected content, and supplemental requirements. A change to any of them starts a new test track and must not be mixed into the prior comparison.

## Exceptions and Routing

Distinguish required evaluation-content problems from handoff provenance requiring confirmation. Evaluate against the product facts, complete brief, eight objects, and locked tags supplied by the caller for this run; this does not independently certify performance or approve a production handoff.

Return `score=null`, `dimension_scores=null`, `pass=false`, and `next_route=complete_input` only when required input is missing, fields or facts contradict one another, tags conflict with the brief in a way that prevents judgment, the image is unreadable, or a material new poster claim lacks support and cannot be classified as correct or incorrect. Set a missing protected object to `null`, preserve complete objects unchanged, and list every blocker in `meta.input_errors`, stating what cannot be judged and the exact missing or conflicting value.

`handoff_provenance` notices such as “reconstructed from old input/PDF and not yet confirmed value-by-value by A,” `needs_human_review=true`, or absent C asset versions/case references are provenance warnings only. Alone they must not enter `draft.input_errors`, stop scoring, demand additional proof for supplied product facts, or reduce scores. When required content is complete and consistent and tags do not conflict, finish scoring against the supplied baseline. Evidence may note that production handoff awaits A/C confirmation, but never treat that reminder as a poster defect or claim production acceptance.

A must confirm reconstructed protected objects and classification before formal production iteration. D's pass means only that this poster meets the consumer threshold for this run. Never delete provenance warnings, set `needs_human_review=false`, or fabricate A/C confirmation to bypass checks. This is one interface boundary and does not create a new test-mode field.

For a normal failure use `next_route=poster_generation_skill`. On pass use `next_route=aesthetic_agent`; A decides whether to invoke it based on the feature flag. Every redrawn image must pass complete hard compliance before D runs again.

## Scripts

`scripts/assemble_input.py` assembles A assets; `scripts/validate_input.py` validates schema and semantics. A model draft contains `subcriteria`, `critical_issues`, `problem_list`, `modify_suggestion`, and `confidence`; legacy drafts with direct five-dimension scores are rejected. Input or image failures may return early through `input_errors` / `image_error`. `scripts/score_evaluation.py draft.json --context input.json --output result.json --details-output scoring-details.json` performs deterministic aggregation. Details remain internal to D and the formal A-D-2.0 schemas do not change. `scripts/run_evals.py` executes interface regression tests; actual image inspection and poster redraw require separate visual integration testing and are never invoked automatically by the script.
