# Consumer Evaluation Agent 1.5.3

This module evaluates an ecommerce poster against a complete A-group brief and locked C-group P-M-S tags. It returns the fixed A-D-2.0 JSON result, deterministic 0–100 scoring, actionable paired feedback, unchanged eight-group protected content, and cumulative regression locks. It evaluates only and never generates images.

## Workflow

1. Assemble the complete normalized source input, C style guide, protected objects, current poster, and optional brief supplement with `scripts/assemble_input.py`.
2. Validate schema and semantics with `scripts/validate_input.py`.
3. Inspect the poster and references, then create a 25-subcriterion internal draft using `SKILL.md` and `references/`.
4. Produce the formal result and separate details with `scripts/score_evaluation.py`.
5. Route pass to the Aesthetic Agent, normal failure to the poster-generation Skill, and missing/conflicting required input to `complete_input`.

Run `scripts/run_evals.py` for deterministic interface regressions. Script tests do not substitute for visual inspection or end-to-end poster testing. See `SKILL.md` for the complete operational contract and the reference documents for scoring anchors and routing.
