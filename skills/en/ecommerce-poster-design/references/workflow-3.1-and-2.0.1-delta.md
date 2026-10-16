# 3.1.0-rc.7 Complete Workflow and Differences from 2.0.1

## Complete Workflow

1. Validate product image, name/category, selling points, price/promotion, marketing goal, canvas ratio, orientation, and format. Exact pixels are optional. Normalize ratio requests deterministically, notify the user of actual dimensions, then create eight protected groups.
2. Classify P-M-S and retrieve C-library guidance. Keep unsupported tags null; choose visual references from exact matching through the default rule and create the style guide.
3. Preflight logos. Treat SVG as authoritative, reject active content/external resources, rasterize to a high-resolution transparent PNG, and record source/derived hashes, dimensions, and ratio.
4. Create a generation plan for product, brand, text, background, layout, and protected regions. ImageGen uses the original product as a reference/edit target and jointly creates product, scene, lighting, contact relationships, and text layout, reserving only the separate logo region. Never create an empty background and then paste the product and full text system. Place the authoritative logo deterministically.
5. Create a candidate with a new `version_id` and image SHA-256. Tool failure without a new image does not count as a redraw.
6. Run HC-01–HC-12, protecting product, quantity, logo, price, promotion, selling points, CTA, and legal copy. A failure triggers targeted redraw and restarts hard compliance.
7. The Consumer Agent inspects the current candidate and submits 25 observations; scripts calculate five dimensions and total. Require total ≥80, every dimension ≥14, no hard failure, and no locked-dimension regression.
8. Only after all five consumer locks, the Aesthetic Agent inspects original size, 360 px thumbnail, product references, and task; it submits 25 observations and scripts calculate six dimensions and total. Require total ≥80 and all six thresholds.
9. On aesthetic failure, create `aesthetic-edit-lock/1.0` from underperforming dimensions, opening only the corresponding local scope and freezing consumer functions, passing aesthetic dimensions, and eight protected groups. The returned image restarts the complete chain.
10. After both agents pass, perform scoreless `FINAL-QUALITY-3.2` arbitration, auditing evidence and locatable defects. Suspiciously high scores trigger one reverse review of the same image without generation.
11. `TEXT_OVERLAP`, `LOGO_FLOATING`, and `PRODUCT_SCENE_COMPOSITE_ARTIFACT` are at least `moderate`, never `minor`; create `final-quality-edit-lock/1.0` and normally apply one or two localized redraws.
12. Every successfully returned image restarts at HC-01, then consumer, aesthetic, and final-quality gates. Any consumer-lock regression rejects it and restores the latest passing baseline.
13. The first image is not a redraw. All later successful returned images share a maximum budget of 8. Output `passed` only when the same candidate passes every gate. On exhaustion choose the best candidate only among hard-compliant and consumer-passed candidates and output `degraded`. Unevaluable input/image yields `blocked`.

## Changes from 2.0.1

| Capability | 2.0.1 | 3.1.0-rc.7 |
|---|---|---|
| Evaluation chain | Hard compliance → consumer | Hard compliance → consumer → aesthetic → final-quality arbitration |
| Aesthetics | No independent professional gate | 25 items, six dimensions, deterministic 100-point scale and per-dimension thresholds |
| After both agents | Consumer pass could proceed to delivery | Both agent passes are upstream recommendations; scoreless final-quality gate is mandatory |
| High-score guard | None | Reverse evidence review of the same candidate when scores are suspiciously saturated |
| Aesthetic edit scope | None | Open only failing dimensions; freeze five consumer functions and eight protected groups |
| Regression | Recheck without cumulative-lock rejection | Any consumer-lock regression rejects the image and restores baseline |
| Logo pipeline | General image input/generation | SVG safety preflight, HD rasterization, reserved-area generation, deterministic placement, hash evidence |
| Product-scene production | No fixed joint-generation boundary | Original product participates in the same generation/edit; no empty background plus pasted product/full text; final gate checks compositing discontinuities |
| Simple visible defects | No final severity routing | Text overlap and floating logo are at least moderate and require local repair |
| Edit contracts | Mainly hard/consumer suggestions | Adds `aesthetic-edit-lock/1.0` and `final-quality-edit-lock/1.0` |
| Binding | Basic request/version records | Also binds image SHA-256, context, upstream results, and evidence; new candidates invalidate old reports |

3.1.0-rc.7 retains the 2.0.1 C library, hard-compliance core, and Consumer Agent 1.5.3. New capabilities reside in the main workflow, aesthetic integration, final-quality arbitration, logo pipeline, and canvas normalization; neither evaluation agent gains generation authority. rc.5.1 adds joint product-scene generation invariants and final defect routing. rc.7 adds only the no-visible-container logo safe-area rule and the prohibition on recombining authoritative lockups. Rubrics, canvas rules, thresholds, and unified budget remain unchanged.
