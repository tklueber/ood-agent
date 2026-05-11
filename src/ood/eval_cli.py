"""``ood eval`` Typer sub-app — Phase 13 Plan 03.

Wires ``EvalRunner`` (Plan 01) and the JSON serializer (Plan 02) behind
the ``eval`` namespace. Provides two subcommands:

- ``run`` — execute the evaluation suite and emit either German human
  output or wire-schema JSON (stdout/file).
- ``cases`` — list available case IDs in a dataset without executing
  the runner.

The exit-code policy is strict per CONTEXT.md D-09:

* Exit 0 on a successful run regardless of pass/fail counts.
* Exit 1 on hard errors: dataset missing/malformed, runner config error
  (``EvalRunnerError``), or ``IndexMissingError`` propagated from
  ``RagEngine.query`` (Plan 13-01 BLOCKER 2 fix).

German user-facing strings (D-04) and the ``»LLM«`` marker (D-07) live
in the ``_emit_human_report`` helper; JSON output reuses
``build_json_report`` / ``dump_json_report`` directly (D-05).

Import safety contract (WARNING 4):
    ``eval_app`` is defined at the top of this module, before the
    ``@eval_app.command(...)`` decorators run. ``ood.cli`` imports
    ``eval_app`` via a deferred import at the bottom of its file, so a
    reverse-direction import (``from ood.eval_cli import eval_app``
    BEFORE ``ood.cli`` has loaded) succeeds even when the partial-load
    re-entry path is exercised.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Annotated

import typer


# IMPORTANT — Import safety contract (WARNING 4):
#
# ``eval_app`` is defined BEFORE the ``from ood.cli import (...)`` statement
# below. When a fresh process imports ``ood.eval_cli`` first, Python begins
# loading this module, reaches ``eval_app = typer.Typer(...)``, then proceeds
# to ``from ood.cli import (...)``. Loading ``ood.cli`` runs that module to its
# deferred-import line at the bottom, which performs
# ``from ood.eval_cli import eval_app``. At that moment ``eval_cli`` is
# partially loaded — but ``eval_app`` has already been bound here, so the
# re-entry finds the symbol and the import succeeds.
eval_app = typer.Typer(
    name="eval",
    help="Lokale Evaluation des OOD Agents über RagEngine.query().",
    no_args_is_help=True,
)


from ood.cli import (  # noqa: E402  (deferred to satisfy reverse-import safety)
    DataDirOption,
    JsonOption,
    KnowledgeDirOption,
    QuietOption,
    StorageDirOption,
    VerboseOption,
    _handle_error,
    _load_valid_settings,
)
from ood.eval_baseline import (  # noqa: E402
    PROPOSED_FIX_TYPES,
    apply_review_decision,
    can_update_baseline,
    load_json_file,
    save_observational_baseline,
    save_review_artifact,
    write_json_file,
)
from ood.eval_report import dump_json_report  # noqa: E402
from ood.eval_runner import EvalRunner, EvalRunnerError, EvalRunResult  # noqa: E402
from ood.evaluation import EvaluationDatasetError, load_evaluation_dataset  # noqa: E402
from ood.models import IndexMissingError  # noqa: E402


DatasetOption = Annotated[
    Path | None,
    typer.Option(
        "--dataset",
        help="Pfad zur Evaluation-Dataset-Datei (überschreibt OOD_EVAL_DATASET).",
    ),
]
CaseIdOption = Annotated[
    str | None,
    typer.Option("--case-id", help="Nur einen Case mit dieser ID ausführen."),
]
OutOption = Annotated[
    Path | None,
    typer.Option(
        "--out", help="Schreibt den JSON-Report zusätzlich in diese Datei."
    ),
]
ReportOption = Annotated[
    Path,
    typer.Option("--report", help="Pfad zu einem schema_version=1 Eval-Report."),
]
BaselineOutOption = Annotated[
    Path | None,
    typer.Option(
        "--out",
        help="Zielpfad für die Baseline-Datei (Default: data/evaluation/baselines/current.json).",
    ),
]
ReviewOutOption = Annotated[
    Path | None,
    typer.Option(
        "--out",
        help="Zielpfad für die Review-Datei (Default: data/evaluation/reviews/<dataset>-<hash>.review.json).",
    ),
]
ReviewPathOption = Annotated[
    Path,
    typer.Option("--review", help="Pfad zur Review-Datei."),
]
DecisionOption = Annotated[
    str,
    typer.Option(
        "--decision", help="Review-Entscheidung: approved, rejected oder deferred."
    ),
]
ReviewerOption = Annotated[
    str | None,
    typer.Option("--reviewer", help="Name oder Kennung der prüfenden Person."),
]
RationaleOption = Annotated[
    str | None,
    typer.Option("--rationale", help="Begründung oder Notiz zur Entscheidung."),
]
BaselineUpdateStatusOption = Annotated[
    str,
    typer.Option(
        "--baseline-update",
        help="Baseline-Status: not_requested, requested, approved oder rejected.",
    ),
]


# ---------------------------------------------------------------------------
# `ood eval run`
# ---------------------------------------------------------------------------


@eval_app.command("run")
def run(
    dataset: DatasetOption = None,
    case_id: CaseIdOption = None,
    out: OutOption = None,
    json_output: JsonOption = False,
    verbose: VerboseOption = False,
    quiet: QuietOption = False,
    knowledge_dir: KnowledgeDirOption = None,
    data_dir: DataDirOption = None,
    storage_dir: StorageDirOption = None,
) -> None:
    """Führe die Evaluation gegen RagEngine.query() aus."""

    try:
        settings = _load_valid_settings(
            knowledge_dir=knowledge_dir,
            data_dir=data_dir,
            storage_dir=storage_dir,
            verbose=verbose,
            quiet=quiet,
        )
    except Exception as error:  # noqa: BLE001 — _handle_error decides re-raise vs exit
        _handle_error(error, verbose=verbose)
        return

    dataset_path = (dataset if dataset is not None else settings.eval_dataset_path).resolve()

    try:
        evaluation_dataset = load_evaluation_dataset(
            dataset_path, knowledge_dir=settings.knowledge_dir
        )
    except FileNotFoundError as error:
        typer.echo(f"Datensatz nicht gefunden: {dataset_path}", err=True)
        raise typer.Exit(code=1) from error
    except EvaluationDatasetError as error:
        typer.echo(f"Datensatz konnte nicht geladen werden: {error}", err=True)
        raise typer.Exit(code=1) from error

    try:
        result = EvalRunner(settings).run(
            evaluation_dataset,
            dataset_path=dataset_path,
            case_id=case_id,
            command_args=tuple(sys.argv[1:]),
        )
    except IndexMissingError as error:
        # Plan 13-01 BLOCKER 2 fix: IndexMissingError now propagates out of
        # EvalRunner.run() rather than being swallowed as N×errored cases.
        # We surface a German message (D-04) and exit 1 (D-09).
        typer.echo(
            "Kein Index gefunden. Bitte zuerst `ood index` ausführen.", err=True
        )
        raise typer.Exit(code=1) from error
    except EvalRunnerError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error
    except typer.Exit:
        raise
    except Exception as error:  # noqa: BLE001 — verbose mode re-raises in _handle_error
        _handle_error(error, verbose=verbose)
        return

    if out is not None:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(dump_json_report(result, indent=2), encoding="utf-8")

    if json_output:
        typer.echo(dump_json_report(result, indent=None))
        return

    if quiet:
        return

    _emit_human_report(result)


# ---------------------------------------------------------------------------
# `ood eval cases`
# ---------------------------------------------------------------------------


@eval_app.command("cases")
def cases(
    dataset: DatasetOption = None,
    json_output: JsonOption = False,
    quiet: QuietOption = False,
    knowledge_dir: KnowledgeDirOption = None,
    data_dir: DataDirOption = None,
) -> None:
    """Liste alle Cases im konfigurierten Dataset auf (ohne Ausführung)."""

    try:
        settings = _load_valid_settings(
            knowledge_dir=knowledge_dir,
            data_dir=data_dir,
            quiet=quiet,
        )
    except Exception as error:  # noqa: BLE001
        _handle_error(error, verbose=False)
        return

    dataset_path = (dataset if dataset is not None else settings.eval_dataset_path).resolve()

    try:
        evaluation_dataset = load_evaluation_dataset(
            dataset_path, knowledge_dir=settings.knowledge_dir
        )
    except FileNotFoundError as error:
        typer.echo(f"Datensatz nicht gefunden: {dataset_path}", err=True)
        raise typer.Exit(code=1) from error
    except EvaluationDatasetError as error:
        typer.echo(f"Datensatz konnte nicht geladen werden: {error}", err=True)
        raise typer.Exit(code=1) from error

    sorted_cases = sorted(evaluation_dataset.cases, key=lambda case: case.id)

    if json_output:
        payload = {
            "dataset": evaluation_dataset.dataset,
            "cases": [
                {"case_id": case.id, "query": case.query} for case in sorted_cases
            ],
        }
        typer.echo(json.dumps(payload, ensure_ascii=False))
        return

    if quiet:
        return

    for case in sorted_cases:
        first_line = case.query.splitlines()[0] if case.query else ""
        typer.echo(f"{case.id}: {first_line}")


# ---------------------------------------------------------------------------
# `ood eval baseline`
# ---------------------------------------------------------------------------


@eval_app.command("baseline")
def baseline(
    report: ReportOption,
    out: BaselineOutOption = None,
    json_output: JsonOption = False,
    quiet: QuietOption = False,
) -> None:
    """Erzeuge eine beobachtende Baseline aus einem Eval-Report."""

    baseline_path = out if out is not None else Path("data/evaluation/baselines/current.json")

    try:
        payload = save_observational_baseline(report, baseline_path)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as error:
        typer.echo(f"Baseline konnte nicht erstellt werden: {error}", err=True)
        raise typer.Exit(code=1) from error

    if json_output:
        typer.echo(
            json.dumps(
                {
                    "artifact_type": payload["artifact_type"],
                    "baseline_path": str(baseline_path),
                    "source_report_hash": payload["source_report_hash"],
                    "baseline_kind": payload["baseline_kind"],
                    "gate_mode": payload["gate_mode"],
                    "thresholds": payload["thresholds"],
                },
                ensure_ascii=False,
            )
        )
        return

    if quiet:
        return

    typer.echo(f"Baseline gespeichert: {baseline_path}")
    typer.echo("Baseline-Typ: observational (keine Schwellwerte)")


# ---------------------------------------------------------------------------
# `ood eval review`
# ---------------------------------------------------------------------------


def _default_review_path(report_path: Path) -> Path:
    report = load_json_file(report_path)
    meta = report.get("meta", {})
    meta_payload = meta if isinstance(meta, dict) else {}
    dataset = str(meta_payload.get("dataset") or "unknown-dataset")
    dataset_hash = str(meta_payload.get("dataset_hash") or "unknownhash")[:8]
    dataset = dataset.replace("/", "-").replace(" ", "-")
    return Path("data/evaluation/reviews") / f"{dataset}-{dataset_hash}.review.json"


@eval_app.command("review")
def review(
    report: ReportOption,
    out: ReviewOutOption = None,
    json_output: JsonOption = False,
    quiet: QuietOption = False,
) -> None:
    """Erzeuge ein Review-Artefakt für fehlgeschlagene Eval-Cases."""

    try:
        review_path = out if out is not None else _default_review_path(report)
        payload = save_review_artifact(report, review_path)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as error:
        typer.echo(f"Review konnte nicht erstellt werden: {error}", err=True)
        raise typer.Exit(code=1) from error

    if json_output:
        typer.echo(
            json.dumps(
                {
                    "artifact_type": payload["artifact_type"],
                    "review_path": str(review_path),
                    "decision": payload["decision"],
                    "baseline_update_status": payload["baseline_update_status"],
                    "case_count": len(payload["cases"]),
                    "proposed_fix_types": sorted(PROPOSED_FIX_TYPES),
                },
                ensure_ascii=False,
            )
        )
        return

    if quiet:
        return

    typer.echo(f"Review gespeichert: {review_path}")
    typer.echo(f"Review-Fälle: {len(payload['cases'])} (failed/errored)")
    typer.echo(
        "Vorgeschlagene Fix-Typen: "
        "baseline_update, corpus_fix, dataset_fix, investigate, query_fix, retrieval_fix"
    )


# ---------------------------------------------------------------------------
# `ood eval decide`
# ---------------------------------------------------------------------------


@eval_app.command("decide")
def decide(
    review: ReviewPathOption,
    decision: DecisionOption,
    reviewer: ReviewerOption = None,
    rationale: RationaleOption = None,
    baseline_update: BaselineUpdateStatusOption = "not_requested",
    out: Path | None = typer.Option(
        None, "--out", help="Zielpfad; Default überschreibt die Review-Datei."
    ),
    json_output: JsonOption = False,
    quiet: QuietOption = False,
) -> None:
    """Speichere eine explizite Review-Entscheidung im Review-Artefakt."""

    target = out if out is not None else review
    try:
        review_payload = load_json_file(review)
        updated = apply_review_decision(
            review_payload,
            decision=decision,
            reviewer=reviewer,
            rationale=rationale,
            baseline_update_status=baseline_update,
        )
        write_json_file(updated, target)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as error:
        typer.echo(f"Review-Entscheidung konnte nicht gespeichert werden: {error}", err=True)
        raise typer.Exit(code=1) from error

    if json_output:
        typer.echo(
            json.dumps(
                {
                    "review_path": str(target),
                    "decision": updated["decision"],
                    "reviewer": updated["reviewer"],
                    "baseline_update_status": updated["baseline_update_status"],
                },
                ensure_ascii=False,
            )
        )
        return

    if quiet:
        return

    typer.echo(f"Review-Entscheidung gespeichert: {target}")


# ---------------------------------------------------------------------------
# `ood eval update-baseline`
# ---------------------------------------------------------------------------


@eval_app.command("update-baseline")
def update_baseline(
    report: ReportOption,
    review: ReviewPathOption,
    out: BaselineOutOption = None,
    json_output: JsonOption = False,
    quiet: QuietOption = False,
) -> None:
    """Aktualisiere die Baseline nur nach genehmigter Review-Entscheidung."""

    baseline_path = out if out is not None else Path("data/evaluation/baselines/current.json")
    try:
        review_payload = load_json_file(review)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as error:
        typer.echo(f"Review konnte nicht geladen werden: {error}", err=True)
        raise typer.Exit(code=1) from error

    if not can_update_baseline(review_payload):
        typer.echo(
            "Baseline-Update erfordert eine genehmigte Review-Entscheidung.",
            err=True,
        )
        raise typer.Exit(code=1)

    try:
        baseline_payload = save_observational_baseline(report, baseline_path)
        updated_review = dict(review_payload)
        updated_review["baseline_update_status"] = "updated"
        write_json_file(updated_review, review)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as error:
        typer.echo(f"Baseline konnte nicht aktualisiert werden: {error}", err=True)
        raise typer.Exit(code=1) from error

    if json_output:
        typer.echo(
            json.dumps(
                {
                    "baseline_path": str(baseline_path),
                    "review_path": str(review),
                    "source_report_hash": baseline_payload["source_report_hash"],
                    "baseline_update_status": "updated",
                },
                ensure_ascii=False,
            )
        )
        return

    if quiet:
        return

    typer.echo(f"Baseline aktualisiert: {baseline_path}")


# ---------------------------------------------------------------------------
# Human-readable German formatter (D-03 / D-04 / D-07 / D-08 / D-10)
# ---------------------------------------------------------------------------


def _emit_human_report(result: EvalRunResult) -> None:
    """Render the German human-readable evaluation report to stdout.

    Format is locked by CONTEXT.md D-03 (header + summary + failures only),
    D-04 (German strings), D-07 (``»LLM«`` marker prefix), D-08 (skipped
    section), and D-10 (errored section). Passed cases are never
    enumerated — only counted in the summary block.
    """

    meta = result.meta
    summary = result.summary

    # Header line 1
    typer.echo(
        f"OOD Evaluation — Datum: {meta.run_started_at} — "
        f"Retrieval-Backend: {meta.retrieval_backend}"
    )

    # Header line 2 — LLM marker prefix (D-07)
    if meta.llm_used:
        typer.echo("»LLM« Cloud-LLM verwendet: ja")
    else:
        typer.echo("Cloud-LLM verwendet: nein")

    typer.echo(f"Datensatz: {meta.dataset} ({meta.dataset_path})")
    typer.echo("")

    # Summary block (D-03)
    typer.echo("Zusammenfassung:")
    typer.echo(f"  Fälle gesamt:        {summary.case_count_total}")
    typer.echo(f"  Bestanden:           {summary.passed_count}")
    typer.echo(f"  Fehlgeschlagen:      {summary.failed_count}")
    if summary.skipped_count > 0:
        skip_reasons = sorted(
            {
                case.skip_reason
                for case in result.cases
                if case.status == "skipped" and case.skip_reason
            }
        )
        reason_label = ", ".join(skip_reasons) if skip_reasons else "—"
        typer.echo(
            f"  Übersprungen:        {summary.skipped_count}"
            f"   (Grund: {reason_label})"
        )
    else:
        typer.echo(f"  Übersprungen:        {summary.skipped_count}")
    typer.echo(f"  Fehler:              {summary.errored_count}")
    typer.echo(
        f"  Aggregiert:          {summary.case_count_aggregated}"
        "   (ohne Übersprungen/Fehler)"
    )
    typer.echo("")

    # Retrieval metrics (aggregated)
    typer.echo("Retrieval-Metriken (aggregiert):")
    if summary.case_count_aggregated == 0:
        typer.echo("  (keine aggregierten Fälle)")
    else:
        retrieval = summary.retrieval
        typer.echo(f"  Hit@1:               {_fmt_rate(retrieval.get('Hit@1'))}")
        typer.echo(f"  Hit@3:               {_fmt_rate(retrieval.get('Hit@3'))}")
        typer.echo(f"  Hit@5:               {_fmt_rate(retrieval.get('Hit@5'))}")
        typer.echo(f"  MRR:                 {_fmt_rate(retrieval.get('mrr'))}")
        typer.echo(
            f"  Source-Recall:       {_fmt_rate(retrieval.get('source_recall'))}"
        )
        typer.echo(
            f"  Forbidden-Source:    {_fmt_rate(retrieval.get('forbidden_source_rate'))}"
        )
    typer.echo("")

    # Ticket-intelligence metrics (aggregated)
    typer.echo("Ticket-Intelligenz (aggregiert):")
    if summary.case_count_aggregated == 0:
        typer.echo("  (keine aggregierten Fälle)")
    else:
        ticket = summary.ticket_intelligence
        typer.echo(
            f"  Intent-Accuracy:     {_fmt_rate(ticket.get('intent_accuracy'))}"
        )
        typer.echo(
            f"  Routing-Accuracy:    {_fmt_rate(ticket.get('routing_accuracy'))}"
        )
        typer.echo(
            f"  Identifier-Recall:   {_fmt_rate(ticket.get('identifier_recall'))}"
        )
        typer.echo(
            f"  Command-Risk:        {_fmt_rate(ticket.get('command_risk_accuracy'))}"
        )
        typer.echo(
            f"  Uncertainty:         {_fmt_rate(ticket.get('uncertainty_accuracy'))}"
        )
    typer.echo("")

    # Failed cases (D-03)
    typer.echo("Fehlgeschlagene Fälle:")
    failed_cases = [case for case in result.cases if case.status == "failed"]
    if not failed_cases:
        typer.echo("  (keine)")
    else:
        for case in failed_cases:
            _emit_failed_case(case)
    typer.echo("")

    # Skipped cases (D-08)
    typer.echo("Übersprungene Fälle:")
    skipped_cases = [case for case in result.cases if case.status == "skipped"]
    if not skipped_cases:
        typer.echo("  (keine)")
    else:
        for case in skipped_cases:
            reason = case.skip_reason or "unbekannt"
            note = ""
            if reason == "llm_required":
                note = " (erwartete LLM-Antwort liegt vor; keine LLM-Credentials konfiguriert)"
            typer.echo(f"  - {case.case_id} — Grund: {reason}{note}")
    typer.echo("")

    # Errored cases (D-10)
    typer.echo("Fehler:")
    errored_cases = [case for case in result.cases if case.status == "errored"]
    if not errored_cases:
        typer.echo("  (keine)")
    else:
        for case in errored_cases:
            typer.echo(f"  - {case.case_id}")
            error_text = case.error or ""
            for trace_line in error_text.splitlines()[:5]:
                typer.echo(f"      {trace_line}")


def _emit_failed_case(case) -> None:  # type: ignore[no-untyped-def]
    """Render one failed case in the German Fehlgeschlagene Fälle block."""

    first_line = case.query.splitlines()[0] if case.query else ""
    truncated = first_line if len(first_line) <= 80 else first_line[:80] + "…"
    typer.echo(f"  - {case.case_id} — \"{truncated}\"")

    expected = ", ".join(case.expected_sources) if case.expected_sources else "(keine)"
    typer.echo(f"      Erwartet:  {expected}")

    actual_pieces = []
    for source in case.actual_sources[:3]:
        path = source.get("path", "?")
        score = source.get("score")
        if isinstance(score, (int, float)):
            actual_pieces.append(f"{path} ({score:.2f})")
        else:
            actual_pieces.append(str(path))
    actual = ", ".join(actual_pieces) if actual_pieces else "(keine)"
    typer.echo(f"      Aktuell:   {actual}")

    mismatch_parts = _collect_mismatch_parts(case)
    if mismatch_parts:
        typer.echo(f"      Mismatch:  {', '.join(mismatch_parts)}")
    else:
        typer.echo("      Mismatch:  (unbekannt)")


def _collect_mismatch_parts(case) -> list[str]:  # type: ignore[no-untyped-def]
    """Return per-key mismatch annotations for a failed case."""

    parts: list[str] = []

    retrieval = case.retrieval_metrics or {}
    for key in ("Hit@1", "Hit@3", "Hit@5"):
        value = retrieval.get(key)
        if value is False:
            parts.append(f"{key}=False")
    if retrieval.get("forbidden_hit") is True:
        parts.append("forbidden_hit=True")
    mrr = retrieval.get("mrr")
    if isinstance(mrr, (int, float)) and mrr < 1.0:
        parts.append(f"mrr={mrr:.2f}")
    source_recall = retrieval.get("source_recall")
    if isinstance(source_recall, (int, float)) and source_recall < 1.0:
        parts.append(f"source_recall={source_recall:.2f}")

    ticket = case.ticket_metrics or {}
    for key in ("intent_match", "routing_match", "uncertainty_match"):
        value = ticket.get(key)
        if value is False:
            parts.append(f"{key}=False")
    identifier_recall = ticket.get("identifier_recall")
    if isinstance(identifier_recall, (int, float)) and identifier_recall < 1.0:
        parts.append(f"identifier_recall={identifier_recall:.2f}")
    command_risk = ticket.get("command_risk_accuracy")
    if isinstance(command_risk, (int, float)) and command_risk < 1.0:
        parts.append(f"command_risk_accuracy={command_risk:.2f}")

    return parts


def _fmt_rate(value: object) -> str:
    """Format a numeric metric value to 4 decimal places or ``n/a``."""

    if isinstance(value, bool):  # bool is a subclass of int — handle explicitly
        return "ja" if value else "nein"
    if isinstance(value, (int, float)):
        return f"{float(value):.4f}"
    return "n/a"


__all__ = ["eval_app"]
