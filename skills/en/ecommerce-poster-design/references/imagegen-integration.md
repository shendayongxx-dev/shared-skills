# ImageGen Integration Contract

## Dependency Boundary

The overall `ecommerce-poster-design` Skill depends on the system `imagegen` Skill and built-in `image_gen` tool. This is the main workflow's generation layer, not part of `modules/consumer-agent`. The Consumer Agent may evaluate a candidate and return a route but must not call an image-generation tool. Do not copy the system Skill's `SKILL.md`, scripts, or references into this directory. Codex maintains that system capability; this document defines only its interface with the ecommerce-poster workflow.

## Invocation Rules

1. Use built-in `image_gen` as the default generation and editing path; do not require an `OPENAI_API_KEY` from the user.
2. Invoke a generation task for a new poster. An aesthetic return must use an edit task with the latest consumer-passed candidate as the sole edit target.
3. Load local product or edit-target images into context through the available image-viewing capability before supplying them to ImageGen. Label each image explicitly as the edit target, product reference, or style reference.
4. Each invocation creates one explicit candidate or performs one targeted change. Invoke and log multiple candidates separately; do not combine different poster requirements in one prompt.
5. The prompt must consume the compiled `style_guide` and carry `protected_content` verbatim. Do not bypass classification and invent prices, discounts, campaign periods, logos, certifications, or selling points.
6. Before an aesthetic-return invocation, validate the route with `scripts/validate_generation_edit_contract.py`. Stop before ImageGen when the contract is missing, crosses versions, lacks all five consumer locks, or overlaps editable and locked dimensions.
7. When `generation_mode=local_edit_only`, prefer masked or layered editing. If the edit scope cannot be constrained reliably, return `blocked`; do not fall back to unconstrained full-image regeneration.

## Product-Scene Joint-Generation Invariants

- Supply the original product image as a product reference or edit target for the first candidate, and establish product, scene, scale, perspective, key light, ambient light, reflection, contact shadow, depth of field, and text layout together in one complete poster generation or edit.
- Do not generate a product-free background first and then mechanically composite a product cutout and complete text system as ordinary layers. Clean product edges or unchanged source pixels do not prove scene integration.
- In the logo pipeline, `base_poster`, “base image,” or “poster without logo” means only that the separate logo has not yet been applied. The file must already contain the product, scene, complete composition, and text layout. The default deterministic post-composite exception is the authoritative separate logo only.
- If ImageGen creates incorrect text, perform a localized text replacement or edit on the complete candidate. Limit repair to the identified text region and preserve the existing hierarchy, support shape, alignment, material, and spatial relationship. Do not rebuild an empty-background/product-layer/text-layer template.
- Product-scene acceptance checks include explainable support/contact, shadow direction and softness matching the key light, no white or black edge, consistent color temperature and environmental reflection, valid perspective and scale, and no conspicuous discontinuity in sharpness, noise, depth of field, or material response.
- A user may explicitly request a transparent-product template, pure-white catalog image, or flat collage. Even then, maintain consistent edges, scale, alignment, and contact relationships. Do not treat this exception as the default degraded path for an ordinary scene-based ecommerce poster.

## SVG Logo Preprocessing and Application

Treat ImageGen local references as readable raster images; direct SVG reading and pixel-exact SVG reproduction are not stable assumptions. When `brand.logo_ref` is SVG, use this fixed chain:

1. Preserve the SVG as the authoritative brand source without overwriting or rewriting it. Run safety preflight and reject scripts, event attributes, external resources, `foreignObject`, and files lacking valid dimensions or `viewBox`.
2. Use the workspace Node and Sharp runtimes with `scripts/prepare_logo_asset.mjs`; rasterize the long edge to 2048 px by default. A large canvas or displayed logo may use 4096 px, but the raster long edge must be at least twice its final display width.
3. The `logo-asset-preflight/1.1` manifest binds absolute SVG/PNG paths, SHA-256 values, dimensions, aspect ratio, actual transparent-pixel state, renderer version, and `crop=false / recolor=false / rotation=0`. An alpha channel whose pixels are all opaque is not proof of transparency; mark it for visual background-artifact review.
4. The first ImageGen prompt must not ask the model to redraw the logo. Reserve a clean, safe, unobstructed, visually natural area within the already joint-generated product, scene, and text composition. Prohibit additional brand text or fake logos. Do not create a placeholder box, backing plate, outline, card, or other visible container. Do not add brand text absent from the authoritative file or recombine symbol, wordmark, or lockup. Place only the symbol when only a symbol asset exists; obtain the authoritative complete asset when a full symbol-wordmark lockup is required.
5. After normalizing the base poster to target canvas size, run `scripts/apply_logo_asset.mjs` with explicit `left/top/width` from the round's layout plan. Preserve aspect ratio and fail on out-of-bounds placement.
6. Run `scripts/verify_logo_application.py` after compositing to create `logo-verification/1.0`. Verify that the current candidate hash equals the composite output hash and validate the source, derived logo, base-poster, and output chain. Do not establish candidate status on failure.
7. Only the final candidate completing `logo_preflight_passed → logo_applied → logo_verified → candidate_ready` may enter HC-01–HC-12, consumer, aesthetic, and final-quality gates. The base poster is not a separate candidate and consumes no separate redraw.

Example:

```text
node scripts/prepare_logo_asset.mjs \
  --input <logo.svg> --output <logo.prepared.png> \
  --manifest <logo.preflight.json> --long-edge 2048 \
  --sharp-module <workspace-node-modules>/sharp

node scripts/apply_logo_asset.mjs \
  --poster <normalized-base.png> --logo <logo.prepared.png> \
  --output <candidate.png> --manifest <logo.application.json> \
  --left <x> --top <y> --width <pixels> \
  --sharp-module <workspace-node-modules>/sharp

python scripts/verify_logo_application.py \
  --candidate <candidate.png> \
  --preflight <logo.preflight.json> \
  --application <logo.application.json> \
  --output <logo.verification.json>
```

If Sharp is unavailable, a controlled SVG renderer may be used only if it produces an equivalent manifest and preserves proportions, color, and transparency. A webpage screenshot, model redraw, or unknown online converter is not equivalent. Return `blocked` when safe conversion is unavailable.

## Prompt Mapping

Map the generation plan to this structure. Omit unsupported fields rather than guessing:

```text
Use case: ads-marketing
Asset type: ecommerce poster
Primary request: <this round's generation or targeted-edit objective>
Input images: <number and role of each image; a deterministically applied logo is not an ImageGen redraw reference>
Scene/backdrop: <derived from style_guide and marketing context>
Subject: <product subject, quantity, packaging components>
Style/medium: <visual style>
Composition/framing: <layout, product share, copy whitespace>
Lighting/mood: <lighting and mood>
Color palette: <one complete selected palette>
Text (verbatim): <all copy that must appear exactly>
Constraints: <protected_content, canvas, fidelity requirements>
Edit contract: <baseline_candidate, editable_aesthetic_dimensions, locked_aesthetic_dimensions, locked_consumer_dimensions>
Avoid: <prohibited content, extra logos, model-redrawn brand marks or brand text, invented information, watermarks>
```

In an edit round, repeat the invariants: modify only regions authorized by `generation_edit_contract.editable_aesthetic_dimensions`; preserve product appearance, packaging text, logo, price, all other `protected_content`, five consumer functions, and passing aesthetic dimensions. The contract takes precedence over a conflicting `modify_suggestion`.

After editing, reevaluate with the latest consumer-passed result as `previous_result`. If `regressed_dimensions` is non-empty, discard the returned image and restore the contract's `baseline_candidate`; do not forward it to aesthetic evaluation.

## Output and Persistence

- An inline result may be used to inspect a preview candidate. Copy or move the final delivery image into the current task's writable workspace and record its absolute path.
- Do not overwrite the user's source image or an existing asset unless explicitly requested; use a versioned filename by default.
- If ImageGen returns dimensions different from the target, save the original result first, then use deterministic high-quality resampling under the main Skill's rules. Apply compliance checks to the final delivery file.

## Failure and Fallback

- Record a tool error when built-in `image_gen` times out, returns no result, or produces an unreadable image. A tool failure is not a valid candidate and consumes no redraw.
- The built-in tool may be retried within the same target round while preserving all protected content and invariants.
- If the built-in tool remains unavailable, explain that CLI/API fallback requires `OPENAI_API_KEY`. Use that path only after explicit user approval.
