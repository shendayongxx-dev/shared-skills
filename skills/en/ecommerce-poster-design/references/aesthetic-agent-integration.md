# Aesthetic Agent 3.0 rc.5 Integration

This workflow is rebuilt from 2.0.1 and integrates `modules/aesthetic-agent` 3.0.0-rc.5 only after hard compliance and consumer evaluation formally pass for the same candidate. Do not mix the frozen legacy Aesthetic v2.4 0–10 scale, independent rounds, or string-based protected-content interface.

## Order

```text
A generates current candidate
→ HC-01–HC-12
→ Consumer Agent A-D-2.0
  ├─ blocked / failed: complete input or redraw within unified budget
  └─ pass=true + all five locks: Aesthetic Agent
      ├─ score=null: complete input/image; no generation
      ├─ pass=false: local edit, then restart at HC-01
      └─ pass=true: validate binding, then final-quality arbitration
```

Every new candidate invalidates all older reports and must traverse the complete chain.

## Assemble Input

```text
python scripts/assemble_aesthetic_input.py \
  --candidate <consumer-input.json> \
  --consumer-result <consumer-result.json> \
  --output <aesthetic-input.json>
```

Output contains only `schema_version`, `candidate`, and `consumer_result`. The assembler validates request, version, poster path, eight protected objects, consumer total and dimensions, regression state, route, and all five locks. It wraps data only and never adds facts.

## Visual Draft and Deterministic Scoring

The visual model inspects the original-size poster, 360 px thumbnail, product assets, and task requirements, then submits the 25 items required by `schemas/evaluation-draft.schema.json`. Each item contains a 0–4 level, locatable evidence, level-4-only enhancement evidence, and a root issue ID.

```text
python modules/aesthetic-agent/scripts/score_evaluation.py \
  --workflow-input <aesthetic-input.json> \
  --draft <evaluation-draft.json> \
  --output <aesthetic-result.json> \
  --details <aesthetic-details.json>
```

The scorer creates the fixed seven-field business result and a separate audit-detail file. The model must not write the total directly.

## Routing and Unified Budget

Run `scripts/route_aesthetic_result.py` with result, consumer result, details, workflow input, configuration, and the global redraw count. Routes are:

- `complete`: current candidate passes the three upstream gates and proceeds to final-quality arbitration;
- `regenerate_then_full_pipeline`: after validating the structured freeze contract, locally edit the last consumer-passed candidate and restart at HC-01;
- `complete_aesthetic_scope`: a critical issue is not bound to an underperforming aesthetic dimension; stop generation for human scope confirmation;
- `complete_aesthetic_input`: evaluation is blocked; complete the input/image without generation;
- `return_best_candidate`: the unified eight-redraw budget is exhausted; return the best historical compliant candidate as `degraded`.

`redraw_attempts` is global across hard compliance, consumer, and aesthetic stages. Increment only for a successfully created candidate; no stage or agent may reset it.

The route's `generation_edit_contract` is generation authorization. It includes the consumer-passed baseline, editable underperforming dimensions only, locked passing aesthetic dimensions, five consumer-function locks, eight immutable protected objects, reference suggestions, prohibited changes, and post-edit checks. Suggestions are advisory and must not override structured locks. Before ImageGen, run `scripts/validate_generation_edit_contract.py`; do not generate after validation failure. Consumer reevaluation of a returned image inherits the prior consumer result and five locks. Any `regressed_dimensions` rejects the image and restores the baseline.

For every non-null score, the router requires the matching `aesthetic-details.json` and cross-checks request, version, poster, protected objects, business result, six thresholds, consumer locks, and `context_hash`.

Validate with the existing aesthetic unit test, integration test, and `validate_aesthetic_integration.py .`.
