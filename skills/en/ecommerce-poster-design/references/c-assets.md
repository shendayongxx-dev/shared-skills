# Reading and Production-Integration Rules for C Classification Assets

> **Current status: C 2.0.1 is integrated.** Formal assets are under `assets/classification/`; six internal reference seeds cover S01–S06. Third-party image binaries are not stored in the public repository. At runtime, use their source URLs and verify content against fixed SHA-256 values.

## A-Group Interface Decisions

1. A's style-guide schema remains `1.0`; record the C-source asset schema separately as `source_schema_version`.
2. The C-source schema is frozen at `2.0.0`, with rules version `2.0.1`. Legacy demo and release-candidate formats remain only for compatibility and are not current production assets.
3. `taxonomy_version=1.0` remains valid because the label ID set did not change during the interface upgrade.
4. A supports both the legacy demo's root `case-index.csv` and the candidate package's `cases/case-index.csv`; formal C 2.0 always uses the latter.
5. A owns rule compilation, case gating, dynamic information hierarchy, and safe fallback. C owns the taxonomy, rule source data, case metadata, source rights, and test evidence.

## Asset Location

Read `assets/classification/` by default. The formal C 2.0 layout is:

- `taxonomy.json`: complete label table;
- `rules.json`: mappings from label combinations to visual rules;
- `cases/case-index.csv`: case index;
- `cases/metadata/*.json`: case metadata;
- `cases/assets/`: optional local case images; original third-party reference seeds are not stored in the public repository;
- `authorization/`: approval records for internal reference use;
- `manifest.json`: file-size and SHA-256 manifest.

A candidate package may run the validator and selector from an external directory. It must not overwrite repository demo assets until it passes.

## Null Classifications

- Classify each dimension only from evidence in the original request. When evidence is insufficient, set its ID to `null`; do not insert a default label.
- When any dimension is null, set `needs_human_review=true`.
- During routing, an unknown dimension may match only a rule whose corresponding dimension is `*`; all known dimensions continue to participate normally.
- In the command-line selector, use `null`, `none`, or `-` for a null value.

## Rule Matching

Use only labels and rules with `status=active`.

1. All three dimensions equal: `exact`.
2. Two dimensions equal and one is `*`: `two_dimension`.
3. One dimension equals and two are `*`: `single_dimension`.
4. All dimensions are `*`: global `R-DEFAULT`.

Within a level, select by descending `priority`; break any remaining tie deterministically by `rule_id`. Never fabricate a rule because no exact combination exists.

## Inheritance Compilation Contract

`extends_rule_id` may reference only an active parent rule. Cycles are prohibited.

- Deep-merge `style` objects recursively by field.
- A child scalar overrides its parent.
- A child array replaces the entire parent array; do not concatenate them.
- A missing child field inherits from the parent.
- An active rule must not explicitly null out a required field.
- Do not inherit `match`, `priority`, `status`, or `rule_id`.
- Use only the selected child rule's `recommended_case_ids`; do not accumulate them from parents.

Every compiled active style must have a valid product share, information density, promotion intensity, and usable palette.

## Palettes and Information Hierarchy

- New rules use `style.palette_sets`. Select exactly one complete palette each time; do not mix colors across sets.
- A wraps legacy demo `style.palette` as one legacy palette for compatibility testing only.
- C supplies the semantic order in `hierarchy_preference`; A generates the final `information_hierarchy` from `protected_content`.
- If price, discount, period, or CTA is absent, do not add that fact to the hierarchy or generated content.

## Case Gates

A formally recommended case must meet all of the following:

1. `review_status=approved`;
2. `is_seed=true`;
3. rights status is `owned`, `licensed`, `permission_granted`, `public_domain`, `internal_authorized`, or `internal_reference_authorized`;
4. it is not `research_reference_only`;
5. case ID, metadata, source URL, and checksum are traceable;
6. a third-party internal-reference seed has `public_repository_allowed=false`, and its original image is not publicly redistributed as a project asset.

Even when referenced by a rule, filter a draft case out of `source_case_ids`; retain it only in `source_case_statuses` and warnings for audit. `is_seed=true` never bypasses a draft or rights gate.

## Meaning of Validation Results

- `valid=true`: structure, references, inheritance, palettes, and manifest are readable; interface integration testing is allowed.
- `production_ready=true`: in addition to being valid, no production blocker exists and at least one eligible seed case is available.
- `valid=true, production_ready=false`: the candidate package may be tested but must not be declared formally integrated.

## Formal Integration Completion Conditions

Set `c_library.status` to `connected` only after all conditions hold:

1. Group C delivers frozen schema, taxonomy, rules, case index, and case metadata.
2. `validate_classification.py` returns both `valid=true` and `production_ready=true`.
3. End-to-end regressions cover exact match, inherited rules, partial null, and all-null inputs.
4. At least six approved internal-reference seeds cover S01–S06 and have source URLs and fixed checksums.
5. Version, change record, and `PROJECT_STATUS.md` are updated.
6. The project owner reviews and merges the integration.

## Asset-Failure Default Style

If files are missing, JSON/CSV cannot be parsed, schemas are incompatible, references fail, or no default rule exists, use:

- white or light neutral background;
- dark, high-contrast text;
- centered product occupying about 55% of the canvas;
- information density 3;
- promotion intensity 3;
- hierarchy: product → product name/core selling point → supplied price and promotion → supplied CTA;
- prohibit low-contrast text, product occlusion, invented promotions, and decorative fake logos.

Set `fallback_level=asset_failure_default` and record both a warning and the failure reason.

## Third-Party Reference-Seed Boundary

The project owner has approved the current six seeds for internal classification, retrieval, style analysis, generation reference, and testing. Approval does not transfer image copyright. The repository must not contain the third-party originals, and output must not deliver a reference image directly as the final design.
