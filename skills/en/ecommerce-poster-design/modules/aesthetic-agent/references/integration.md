# Integration into Workflow A

Order: A generates → hard compliance → Consumer Agent. Consumer `score=null` completes input; consumer failure returns to A; consumer pass with all five locks invokes this Agent. Aesthetic `score=null` completes input/image with no generation; failure creates a consumer-locked local edit and the new image restarts hard compliance; pass proceeds to final-quality arbitration.

Input schema is `A-D-AESTHETIC-3.0` with exactly `candidate` (complete A-D-2.0 consumer input) and `consumer_result` (formal output for that candidate). Poster path, request ID, version ID, and eight protected objects must bind the same candidate. A separately logs image SHA-256, hard report, module/model versions, and does not add them to the seven-field aesthetic response. Upstream requires consumer total ≥80, each dimension ≥14, `pass=true`, `hard_fail=false`, `next_route=aesthetic_agent`, and five accumulated locks.

The visual model emits an internal draft matching `schemas/evaluation-draft.schema.json`, with all 25 rubric keys and fields `level`, `evidence`, `enhancement_evidence`, and `root_issue_id`. Use one root ID for one root cause. On failure output at most three paired problems/suggestions; each suggestion states editable scope, prohibited scope, consumer locks, and acceptance. If the image is unreadable or a critical fact is missing, set non-empty `evaluation_blocked`; the scorer outputs `score=null`.

Run `scripts/score_evaluation.py` with workflow input, draft, result, and details paths. The script validates upstream state, protected objects, item set, levels, evidence, level-4 enhancement evidence, recommendation structure, and hard issues before calculating. The result is the business response; details are A's internal audit.

The formal response contains only `agent_name`, `score`, `pass`, `problem_list`, `modify_suggestion`, `protected_content`, and `meta`. Consumer and aesthetic totals are both percentages but measure different dimensions and must not be added or averaged. Aesthetic 80 does not replace six per-dimension thresholds.

On failure A sends only recommendations for underperforming dimensions to production, together with current poster, original product assets, eight protected groups, and consumer locks. A creates a new version ID/hash after generation; all old scores expire. Prefer masks/layers, but regardless of method inspect the actual output rather than claiming preservation from the prompt.
