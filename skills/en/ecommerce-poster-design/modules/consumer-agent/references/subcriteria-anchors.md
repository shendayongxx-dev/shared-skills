# 25 Subcriterion Anchors and Evidence

IDs, names, and weights in `assets/rubric.json` are authoritative. Every item states image location, visible fact, and impact; do not write only “good.” Do not claim measured recognition time or conversion without testing. Unreadable images or absent critical input route as exceptions, not level 0. Apply adjacent boundaries in `candidate-boundaries.md`; factual items use confirmed-correct = 4 and confirmed-wrong = 0 rather than hiding errors in middle levels.

- `D1_1`: 0 unrecognizable; 2 recognizable with obstruction/unclear detail; 3 clear subject; 4 complete, clear identifying structure.
- `D1_2`: 0 hard to find; 2 competes with decoration; 3 readily found; 4 unmistakable primary visual priority at fixed display size without sacrificing required information.
- `D1_3`: 0 wrong/missing brand; 2 difficult to read; 3 clear; 4 unambiguous and consistent with supplied assets. Without separate logo, judge existing brand text only.
- `D1_4`: 0 identity-changing alteration; 2 key feature partly hidden; 3 visible and basically consistent; 4 all reference-supported key features complete. Explicit alteration also hard-fails.
- `D1_5`: 0 misleading category/use; 2 guessed; 3 clear; 4 name, appearance, and use mutually support one another.
- `D2_1`: 0 required selling point missing/wrong; 2 partial; 3 all present; 4 complete with task priority unmistakable. Explicit omission also hard-fails.
- `D2_2`: 0 unreadable; 2 effortful; 3 easy; 4 concise, unambiguous, with any diagram accurately corresponding.
- `D2_3`: 0 no benefit; 2 abstract benefit/parameter; 3 usable outcome; 4 feature/parameter directly connected to a concrete result.
- `D2_4`: 0 unsupported new fact; 2 generic support; 3 specific input-supported fact; 4 key benefit has complete, matching, properly scoped supplied support; do not require unsupplied certification.
- `D2_5`: 0 conflicts with direction; 2 relevant but weak priority; 3 relevant to M/S; 4 primary selling point directly answers the locked need.
- `D3_1`: factual: complete correct price/offer nature, value, currency, unit, and qualifiers = 4; confirmed error or required omission = 0 and hard fail; missing input first routes `complete_input`. Visibility belongs to D3_2.
- `D3_2`: 0 undiscoverable/unreadable; 2 effortful; 3 clear; 4 transaction core has explicit priority and amount/unit/type stay associated.
- `D3_3`: 0 confirmed wrong or required condition missing and hard fail; 2 partial; 3 complete/readable; 4 closely associated, clear, and unambiguous.
- `D3_4`: 0 required CTA absent; 2 vague action; 3 clear next step; 4 clear, easy to find, and appropriate to object/eligibility. Never claim clickability.
- `D3_5`: 0 confused transaction logic; 2 repeated searching; 3 clear order; 4 benefit, condition, and action connect without a misleading jump.
- `D4_1`: 0 obstructs known P needs; 2 partial; 3 appropriate reception; 4 key benefits and reading organization clearly target the task. No age stereotypes.
- `D4_2`: 0 contradicts M; 2 weak; 3 selling point responds generally; 4 M-related core benefit has primary-zone priority and theme, claim, and evidence jointly support the same motivation. Cite both priority and consistency.
- `D4_3`: 0 conflicting use; 2 atmosphere/weak relation only; 3 real use relation; 4 benefit directly connects to action, structure, copy, or environment. No person/background is mandatory.
- `D4_4`: 0 product, benefit, and scene contradict; 2 partly disconnected; 3 consistent; 4 mutually reinforce the same task need.
- `D4_5`: 0 clear need mismatch; 2 ambiguous; 3 no clear mismatch; 4 positioning boundary is explicit. Other brief-authorized scenes are not violations.
- `D5_1`: factual: no promise beyond input and necessary qualifiers complete = 4; confirmed exaggeration = 0 and hard fail; unverifiable material fact routes `complete_input`.
- `D5_2`: 0 misleading evidence; 2 weak fact-confidence link; 3 confirmed fact supports claim; 4 understandable evidence with clear applicability/comparison directly supports the specified confidence. Parameters/asterisks alone do not upgrade it; avoid D2 double deduction.
- `D5_3`: 0 confirmed identity deception; 1 major ownership obstacle; 2 ambiguous; 3 brand-product relation clear; 4 fully consistent with supplied asset/identity without ambiguity. “Official” is not authorization evidence.
- `D5_4`: 0 critical concern answered incorrectly; 2 generic/limited assurance; 3 each concern frozen before viewing has a specific input-supported answer; 4 all answers and necessary conditions are clear with no critical gap. Never choose concerns after viewing.
- `D5_5`: 0 confirmed false reason; 1 action conflicts with benefit; 2 generic CTA/weak link; 3 confirmed product or transaction benefit motivates action; 4 product value, applicable offer, and action connect unambiguously without invented urgency.

For D3_1–D3_4, `level=null` is allowed only if the corresponding field is empty and the original brief does not require it; include `not_applicable_reason` and evidence. Missing required input must use `complete_input`. D3_5 always evaluates reading order. Renormalize applicable D3 weights to 20. Keep task, tags, and rubric version fixed per round; a rubric update creates a new baseline.
