# Hard-Compliance Checks

For every item output `pass/fail`, evidence, issue location, and repair guidance. Treat an unverifiable item as failed; never substitute aesthetic judgment for factual verification.

| ID | Check | Pass condition |
|---|---|---|
| HC-01 | Product fidelity | Product category, appearance, color, and key details are not replaced or materially altered. |
| HC-02 | Product quantity | Quantity matches the input. If unspecified, do not imply a misleading bundle quantity. Boxes, bottles, refills, accessories, and other components must match the quantity semantics; repeated packaging or mirroring must not suggest a free extra item. |
| HC-03 | Price and unit | Price, currency, unit, original price, and final price all match the input. |
| HC-04 | Promotion and period | Discounts, threshold offers, gifts, and campaign dates are neither omitted, rewritten, nor exaggerated. |
| HC-05 | Logo and brand | When `logo_ref` is non-empty, the final candidate contains exactly one independent logo deterministically composited from that authoritative source, with `logo-asset-preflight/1.1`, `logo-application/1.0`, and `logo-verification/1.0` manifests. The candidate hash equals the composite output hash. Verify source/derived/composite hashes, proportion, color, orientation, complete boundary, uniqueness, and absence of unintended rectangular backgrounds, borders, white/black edges, or alpha halos. The model must not redraw, stretch, rotate, crop, recolor, replace, or duplicate it. When `logo_ref` is empty, do not create an independent brand mark; a trademark already printed on the product package does not authorize adding another independent logo. |
| HC-06 | Selling-point completeness | Required selling points and legal copy are complete, with no unsupported efficacy claim. |
| HC-07 | Text correctness | No typo, garbling, mistranslation, duplication, truncation, or semantic change. |
| HC-08 | Readability | Text is unobstructed and font size, contrast, and line spacing are readable. |
| HC-09 | Bounds and safe areas | Product, logo, price, CTA, and legal copy are inside bounds and not cropped. |
| HC-10 | Canvas and format | Pixel width/height, ratio, language, and file format exactly match the input. If the generator returns approximate dimensions, deterministically resample at high quality, then recheck safe areas and readability. |
| HC-11 | Prohibited content | No element or expression explicitly prohibited by the input or `style_guide` appears. |
| HC-12 | `protected_content` | Every protected value is identical to input. |

## Routing

- Any failed check: create a structured `problem_list` and request a targeted redraw.
- After redraw: restart at HC-01. If editing times out or yields no image, record the tool error and perform an equivalent regeneration in the same target round using the original reference, complete protected content, and one repair objective.
- All pass: continue downstream.
- Budget exhausted: choose the candidate with the fewest and least severe issues, output `degraded`, and list unresolved issues.

Hard compliance must not include subjective claims such as “not premium enough” or “average aesthetics.”

## Counting and Fallback

- Increment the global redraw count only when a new inspectable candidate is created. Timeout, empty output, or unreadable output is a tool error, not a candidate.
- Prefer a local edit of the previous candidate. If edit capability repeatedly fails or is unavailable, perform an equivalent regeneration in the same target round.
- Equivalent regeneration must include the original product reference, previous candidate when supported, all eight `protected_content` groups, locked dimensions, and the single repair objective. It must not alter price, promotion, logo, product quantity, or any protected fact.
- Normalize a new candidate to exact canvas dimensions before rerunning HC-01–HC-12. A requirement written in the prompt is not evidence that the output passes.
