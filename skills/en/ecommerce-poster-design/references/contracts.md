# Input, Output, and Logging Contracts

## Input Contract

Accept natural-language input or an equivalent structured input. Normalize the canvas request first:

```json
{
  "aspect_ratio": "4:5",
  "orientation": "vertical",
  "format": "png",
  "width": null,
  "height": null,
  "language": "zh-CN",
  "platform_size": null
}
```

Aspect ratio, orientation, and output format are required in the normalized result. When the user does not state an orientation separately, derive it from the ordered width-to-height ratio without asking. Exact `width` and `height` are optional, but they must be supplied together. Without exact pixels, use 1080 px as the minimum short edge and multiply the reduced ratio by the smallest integer that satisfies it: `1:1 → 1080×1080`, `4:5 → 1080×1350`, `3:4 → 1080×1440`, `9:16 → 1080×1920`, and `16:9 → 1920×1080`. Set `platform_size` only when the delivery platform has explicit dimensions; it overrides the ratio default. After selecting a platform or default size, tell the user the actual dimensions before calling ImageGen without requiring another confirmation. Do not return `blocked` merely because absolute pixels are absent or orientation can be derived from the ratio.

Run:

```text
python scripts/resolve_canvas.py --input <request.json> --output <normalized-request.json>
```

The script replaces the original `canvas` with downstream-compatible exact `width`, `height`, `format`, and `language` fields. It also adds `canvas_resolution` at the root to record the original requirement, resolution method, platform override state, and user notice. Return an input error only when an explicit orientation conflicts with the ratio, only one pixel dimension is supplied, exact pixels conflict with the ratio, or the format is missing.

After canvas resolution, the standard input before execution is:

```json
{
  "request_id": "REQ-001",
  "product": {
    "image_refs": ["product image path or attachment reference"],
    "name": "product name",
    "category": "product category",
    "selling_points": ["confirmed selling point"],
    "quantity": null
  },
  "brand": {
    "name": "brand name",
    "logo_ref": "logo path or attachment reference",
    "required_elements": [],
    "forbidden_elements": []
  },
  "commerce": {
    "price_text": "complete price text",
    "promotion_text": "complete promotion text",
    "promotion_period": "campaign period",
    "legal_text": "legal or restrictive text"
  },
  "marketing": {
    "goal": "marketing objective",
    "channel": "delivery channel",
    "usage_context": "usage or purchase context",
    "cta": "call to action"
  },
  "canvas": {
    "width": 1080,
    "height": 1350,
    "format": "png",
    "language": "zh-CN"
  }
}
```

`quantity` may be null when unclear, but generation must not add product units on its own. `logo_ref` may be empty when no logo exists; do not draw a fake logo. The `canvas` passed to the Consumer Agent always contains positive integer dimensions, so do not loosen the downstream A-D-2.0 schema.

`canvas.language` must select exactly one supported output language: Chinese-only or English-only. The final poster must use copy in that selected language supplied or explicitly confirmed by the user. Chinese-English bilingual output is not supported, and the two language sets must not be combined in one poster. Both single-language modes enter the same A-D-2.0, hard-compliance, aesthetic, and final-quality chain; neither creates a separate score or budget. Preserve all selected-language copy placed in `protected_content` exactly as confirmed by the user. Do not translate, delete, merge, split, or rewrite it during generation or reevaluation. If required copy in the selected language has not been supplied or confirmed, treat it as missing input.

## Protected Content

```json
{
  "product_identity": [],
  "product_quantity": null,
  "brand_and_logo": [],
  "price_and_unit": [],
  "promotion_and_period": [],
  "selling_points": [],
  "cta": [],
  "legal_text": []
}
```

Every redraw must inherit these values exactly. Only new facts supplied by the user may change protected content.

## Style Guide

```json
{
  "schema_version": "1.0",
  "source_schema_version": "2.0.0",
  "taxonomy_version": "1.0",
  "asset_version": "2.0.1",
  "tags": {"audience_id": null, "motivation_id": "M01", "scenario_id": "S01"},
  "classification_evidence": [],
  "confidence": {"audience": 0.0, "motivation": 0.0, "scenario": 0.0},
  "needs_human_review": true,
  "source_rule_ids": ["R-201"],
  "inheritance_chain": ["R-201"],
  "source_case_ids": [],
  "source_case_statuses": [],
  "source_case_references": [],
  "fallback_level": "single_dimension",
  "selected_palette_set": {"palette_id": "R-201-P1", "colors": []},
  "palette": [],
  "typography": {},
  "layout": {},
  "info_density": 3,
  "promotion_intensity": 3,
  "cta_guidance": "",
  "prohibited_styles": [],
  "warnings": []
}
```

`fallback_level` must be one of `exact`, `two_dimension`, `single_dimension`, `global`, or `asset_failure_default`.

- `schema_version` is the A-output style-guide contract version; `source_schema_version` is the C-source asset version. Do not conflate them.
- When classification evidence is insufficient, set the corresponding tag to null and set `needs_human_review=true`; an unknown dimension may match only `*`.
- Order `inheritance_chain` from the parent rule to the selected rule.
- `selected_palette_set` is the one complete palette selected for this request. The compatibility field `palette` must equal its `colors`; do not mix colors across palettes.
- `source_case_ids` contains only cases that pass review, rights, and seed gates. Record filtered cases only in `source_case_statuses` and warnings.
- `source_case_references` provides the source URL, fixed SHA-256, and permitted scope for internal reference seeds. Third-party images are internal references, not project-owned assets, and must not be redistributed from the public repository.
- A generates `layout.information_hierarchy` from `protected_content` and C's hierarchy preference. Do not add a price, deadline, or CTA that was not supplied.

## Hard-Compliance Result

```json
{
  "passed": false,
  "round": 1,
  "problem_list": [{
    "check_id": "HC-03",
    "severity": "critical",
    "location": "price area",
    "evidence": "the input price and poster price do not match",
    "repair_action": "restore the complete input price and unit"
  }]
}
```

Severity must be `critical`, `major`, or `minor`. Do not mark the result as passed when any critical or major issue exists.

## Per-Round Log

Save at least:

- `request_id`, Skill version, schema version, and asset version;
- input summary and protected content;
- classification tags, evidence, confidence, rule IDs, and case IDs;
- generation configuration and output reference;
- hard-compliance result;
- this round's revision recommendation and next step;
- round number, start and end time, and duration;
- warnings.

When image editing fails, also record `tool_error` (tool, error type, duration, and whether it produced a candidate) and `fallback_mode`. A tool error that produces no inspectable image does not count as a separate redraw; a later successful equivalent candidate counts as one redraw.

Normalize the final poster to the request's exact dimensions before HC-10. Record original generation size, normalization algorithm, and normalized size in the generation configuration. Recheck safe areas, logo, text, and product form after normalization.

For a round entering consumer evaluation, also save:

- the A-D-2.0 input reference, Consumer Agent version, and `context_hash`;
- formal consumer result, five dimension scores, evidence, locked dimensions, and regressed dimensions;
- reference to the internal 25-subcriterion scoring details;
- `next_route` and the main workflow's interpretation;
- global cumulative redraw count, which must not reset on an agent call.

## Final Output Status

- `passed`: all hard-compliance checks pass;
- `degraded`: the limit is reached; return the best candidate and unresolved issues;
- `blocked`: stop automatic iteration because required input is missing or consumer-evaluation input conflicts, is missing, or contains an unreadable image.

In 2.0, `passed` additionally requires Consumer Agent approval. When the consumer returns `next_route=aesthetic_agent`, the main workflow interprets that as completion for that version because the aesthetic feature flag is disabled, rather than calling the Aesthetic Agent.
