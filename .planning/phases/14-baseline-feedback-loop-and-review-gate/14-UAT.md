---
status: testing
phase: 14-baseline-feedback-loop-and-review-gate
source:
  - 14-01-SUMMARY.md
  - 14-02-SUMMARY.md
  - 14-03-SUMMARY.md
started: 2026-05-11T11:31:14Z
updated: 2026-05-11T11:54:01Z
---

## Current Test

number: 3
name: Record Review Decision
expected: |
  Running `ood eval decide --review <review.json> --decision approved --reviewer <name> --rationale <note> --baseline-update requested` updates the review file with the top-level decision, reviewer, rationale, and baseline update status while preserving each case's existing `proposed_fix_type` and `proposed_fix_notes`.
awaiting: user response

## Tests

### 1. Create Observational Baseline
expected: Running `ood eval baseline --report <schema_version=1 report> --out <baseline.json>` creates a JSON baseline file. The file contains `artifact_type: ood_eval_baseline`, `baseline_kind: observational`, `gate_mode: review_required`, `thresholds: null`, a source report hash, and the embedded original report.
result: issue
reported: "ood eval baseline --report <schema_version=1 report> --out <baseline.json>\nzsh: parse error near `\\n'"
severity: blocker

### 2. Create Failed-Case Review Artifact
expected: Running `ood eval review --report <report-with-failures.json> --out <review.json>` creates a review JSON file containing only failed and errored cases. Each review case includes expected/actual evidence, `decision: deferred`, `proposed_fix_type: investigate`, and `proposed_fix_notes: null`.
result: issue
reported: "❯ ood eval review --report <report-with-failures.json> --out <review.json>\nzsh: parse error near `\\n'"
severity: blocker

### 3. Record Review Decision
expected: Running `ood eval decide --review <review.json> --decision approved --reviewer <name> --rationale <note> --baseline-update requested` updates the review file with the top-level decision, reviewer, rationale, and baseline update status while preserving each case's existing `proposed_fix_type` and `proposed_fix_notes`.
result: [pending]

### 4. Enforce Gated Baseline Update
expected: Running `ood eval update-baseline --report <report.json> --review <review.json> --out <baseline.json>` refuses to write a baseline for deferred, rejected, missing-reviewer, or not-requested reviews with the German gate message. After an approved review with requested or approved baseline update status, it writes the observational baseline and marks the review's top-level `baseline_update_status` as `updated`.
result: [pending]

### 5. Follow Documented Local Loop
expected: README contains a `Baseline and review gate` workflow showing mock data generation, reindexing, smoke query, evaluation, baseline creation, review creation, decision recording, and gated baseline update. It states the first baseline remains observational with `thresholds` null, proposed fix fields are machine-readable, and metric improvement alone is not accepted improvement.
result: [pending]

## Summary

total: 5
passed: 0
issues: 2
pending: 3
skipped: 0
blocked: 0

## Gaps

- truth: "Running `ood eval baseline --report <schema_version=1 report> --out <baseline.json>` creates a JSON baseline file. The file contains `artifact_type: ood_eval_baseline`, `baseline_kind: observational`, `gate_mode: review_required`, `thresholds: null`, a source report hash, and the embedded original report."
  status: failed
  reason: "User reported: ood eval baseline --report <schema_version=1 report> --out <baseline.json>\nzsh: parse error near `\\n'"
  severity: blocker
  test: 1
  artifacts: []
  missing: []
- truth: "Running `ood eval review --report <report-with-failures.json> --out <review.json>` creates a review JSON file containing only failed and errored cases. Each review case includes expected/actual evidence, `decision: deferred`, `proposed_fix_type: investigate`, and `proposed_fix_notes: null`."
  status: failed
  reason: "User reported: ❯ ood eval review --report <report-with-failures.json> --out <review.json>\nzsh: parse error near `\\n'"
  severity: blocker
  test: 2
  artifacts: []
  missing: []
