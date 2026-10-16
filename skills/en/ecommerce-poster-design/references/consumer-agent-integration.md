# Consumer Agent Integration

## Version and Boundary

- Main workflow: 3.1.0-rc.7, retaining interface A-D-2.0;
- Consumer module: `modules/consumer-agent` 1.5.3;
- Both consumer and aesthetic feature flags are enabled; enter aesthetics only after formal consumer approval and all five locks;
- 1.0.0 remains the no-agent ablation baseline and must not be overwritten.

The consumer module evaluates once and returns JSON. The main workflow owns generation, hard compliance, logs, routing, unified redraw count, and stopping conditions.

## Input Assembly

Every round preserves A's complete normalized input, C's complete `style_guide`, and all eight `protected_content` groups. Do not delete legacy fields merely to integrate the module, and never infer product facts from the case library.

Use `assemble_input.py` with source, style, protected content, current poster, and output, then run `validate_input.py`. Supply an explicit theme, required-information list, or brand character through `--brief-supplement`. From round two onward, use `--previous`, `--iteration`, and `--version` to inherit the latest normal result that completed all five dimensions. A `complete_input` result cannot replace the normal historical baseline.

`brief-supplement` accepts `theme`, `required_information`, and `brand_requirements`, plus legacy aliases `brand_tone` and `test_requirement`; the latter four may be a string or string array. Unknown fields must produce an explicit list of supported fields rather than a Python unexpected-keyword exception.

## Evaluation and Calculation

The evaluator must inspect the current poster and all relevant product references and create an internal draft according to the consumer `SKILL.md`, rubric, 25 anchors, and candidate boundaries. Then run the deterministic aggregator. Do not use the legacy 0–10 scale, simplified seven-field JSON, or drafts in which the model directly supplies the five totals. Formal approval requires total ≥80, every dimension ≥14, no hard failure, and no locked-dimension regression.

## Routing

| Result | Main-workflow action |
|---|---|
| `pass=true`, `next_route=aesthetic_agent` | Preserve current candidate as the latest consumer-passed baseline and enter aesthetics with all five locks. |
| `next_route=poster_generation_skill` | Targeted redraw with paired issues/suggestions, eight protected groups, and locked dimensions; then rerun complete hard compliance and reevaluate. |
| `next_route=complete_input` | Stop automatic redraw and output `blocked` with specific input errors. |
| `hard_fail=true` | Never pass; repair and restart complete hard compliance. |
| non-empty `regressed_dimensions` | Reject the returned image immediately, restore the latest consumer-passed candidate, and retry only from that baseline under a tightened aesthetic edit contract. |

Hard compliance and consumer edits share `max_redraw_attempts`. Every regeneration restarts HC-01–HC-12. On exhaustion output `degraded`; never fabricate `pass=true`. Tool timeout, empty output, or unreadable output follows the hard-compliance fallback and increments the count only if a new candidate is created.

For reevaluation after an aesthetic edit, `--previous` must point to the latest formal consumer-pass result before aesthetics, never the failed returned image or an empty `complete_input` result. `loop_state.locked_dimensions` must retain all five dimensions. On regression, the router returns `candidate_disposition=reject` and `restore_last_consumer_pass=true`; the failed image cannot overwrite the baseline.

Interpret results with `scripts/route_consumer_result.py`, the version configuration, and the current global redraw count. Validate using the existing consumer integration validation, routing test, and module eval runner. Real poster inspection and redraw still require end-to-end visual testing.
