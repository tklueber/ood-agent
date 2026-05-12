# Phase 14: Baseline, Feedback Loop, and Review Gate - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in `14-CONTEXT.md`; this log preserves the alternatives considered.

**Date:** 2026-05-11
**Phase:** 14-baseline-feedback-loop-and-review-gate
**Areas discussed:** Baseline artifact, Review records, Command flow, Acceptance gate

---

## Area Selection

| Option | Description | Selected |
|--------|-------------|----------|
| All four | Discuss baseline artifact, review records, command flow, and acceptance gate. | yes |
| Baseline artifact | Where/how the first baseline is saved and what metadata makes it observable rather than pass/fail gated. | |
| Review records | What failed-case evidence and reviewer decisions must be captured. | |
| Command flow | How users run baseline creation, review generation, and baseline update from the CLI. | |
| Acceptance gate | What explicit decision is required before corpus/retrieval changes or baseline updates are accepted. | |

**User's choice:** All four.
**Notes:** All four areas affect command/API shape or persisted artifacts.

---

## Baseline Artifact

| Option | Description | Selected |
|--------|-------------|----------|
| Explicit snapshot | Add a command that writes a reviewed JSON baseline under a deterministic baseline path; no auto-promotion. | yes |
| Reuse --out only | Keep using `ood eval run --out` and document a naming convention, with minimal new code. | |
| Auto-save every run | Every eval run writes a timestamped report automatically; convenient but noisier and less explicit. | |

**User's choice:** Explicit snapshot.
**Notes:** Baseline creation should be deliberate and observational, not an automatic promotion from every run.

---

## Review Records

| Option | Description | Selected |
|--------|-------------|----------|
| Evidence plus decision | Failed case evidence, proposed next action, reviewer decision, rationale, owner/date, and baseline-update status. | yes |
| Evidence only | Capture expected-vs-actual and metrics, but leave decisions outside the artifact. | |
| Decision only | Capture high-level approve/reject/defer without full per-case evidence details. | |

**User's choice:** Evidence plus decision.
**Notes:** Review artifacts must be useful both for a human reviewer and for downstream automation that needs to know whether a change was approved.

---

## Command Flow

| Option | Description | Selected |
|--------|-------------|----------|
| Extend ood eval | Keep under `ood eval` with subcommands like `baseline`, `review`, and update/apply action. | yes |
| Separate commands | Create top-level commands like `ood baseline` or `ood review`; simpler names but expands CLI surface. | |
| Docs-only flow | Do not add new commands beyond `ood eval run`; document manual steps for now. | |

**User's choice:** Extend ood eval.
**Notes:** This carries forward Phase 13's namespace decision and avoids CLI naming churn.

---

## Acceptance Gate

| Option | Description | Selected |
|--------|-------------|----------|
| Explicit approved decision | Changes can be accepted only when review status is `approved`; rejected/deferred never updates baseline. | yes |
| Manual file edit | User updates baseline/review files manually; no code-enforced state transition. | |
| Metric improvement enough | Automatically accept when aggregate metrics improve; faster but conflicts with no-premature-threshold posture. | |

**User's choice:** Explicit approved decision.
**Notes:** Metric improvement alone must not update the baseline or mark a change accepted in Phase 14.

---

## Planner Discretion

| Option | Description | Selected |
|--------|-------------|----------|
| Planner decides | Keep context decision-level and let the planner choose exact names/paths consistent with the codebase. | yes |
| Refine names | Discuss exact command names and baseline/review file paths before writing context. | |

**User's choice:** Planner decides.
**Notes:** Exact command names, flags, and file paths are left to the planner, constrained by the decisions above.

---

## Deferred Ideas

- Hard CI regression thresholds remain deferred to EVAL-10.
- Historical trend dashboards remain deferred until baseline mechanics exist.
- LLM-as-judge remains deferred and privacy-gated.
