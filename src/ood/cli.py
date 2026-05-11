from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from ood.config import Settings, load_settings
from ood.mock_corpus import MockCorpusResult, generate_mock_corpus
from ood.mock_validation import MockValidationResult, validate_mock_corpus
from ood.models import IndexMissingError, IndexResult, IndexStatus, QueryResult, UpdateResult
from ood.knowledge_quality import KnowledgeQualityReport, audit_knowledge_corpus
from ood.rag import RagEngine


app = typer.Typer(
    name="ood",
    help="CLI for the OOD Agent knowledge workflow.",
    no_args_is_help=True,
)
console = Console()

JsonOption = Annotated[bool, typer.Option("--json", help="Emit machine-parseable JSON.")]
VerboseOption = Annotated[
    bool,
    typer.Option("-v", "--verbose", help="Show diagnostic context and exception details."),
]
QuietOption = Annotated[bool, typer.Option("-q", "--quiet", help="Suppress non-essential output.")]
KnowledgeDirOption = Annotated[
    Path | None,
    typer.Option("--knowledge-dir", help="Override the Markdown knowledge directory."),
]
DataDirOption = Annotated[
    Path | None,
    typer.Option("--data-dir", help="Override the runtime data directory."),
]
StorageDirOption = Annotated[
    Path | None,
    typer.Option("--storage-dir", help="Override the retrieval storage directory."),
]
MockTargetDirOption = Annotated[
    Path,
    typer.Option("--target-dir", help="Directory where the generated mock corpus will be written."),
]
MockCorpusDirOption = Annotated[
    Path,
    typer.Option("--corpus-dir", help="Directory containing mock Markdown files to validate."),
]
QualityCorpusDirOption = Annotated[
    Path,
    typer.Option("--corpus-dir", help="Directory containing OOD-KB Markdown articles to audit."),
]


def _load_valid_settings(
    *,
    knowledge_dir: Path | None = None,
    data_dir: Path | None = None,
    storage_dir: Path | None = None,
    verbose: bool = False,
    quiet: bool = False,
) -> Settings:
    """Load settings and fail early if the configuration shape is invalid."""

    overrides: dict[str, object] = {"verbose": int(verbose), "quiet": quiet}
    if knowledge_dir is not None:
        overrides["knowledge_dir"] = knowledge_dir
    if data_dir is not None:
        overrides["data_dir"] = data_dir
    if storage_dir is not None:
        overrides["storage_dir"] = storage_dir
    return load_settings(**overrides)


def _format_paths(settings: Settings) -> str:
    return (
        f"knowledge_dir={settings.knowledge_dir} "
        f"data_dir={settings.data_dir} "
        f"storage_dir={settings.storage_dir}"
    )


def _emit_index_result(
    *,
    command: str,
    result: IndexResult,
    json_output: bool,
    verbose: bool,
    quiet: bool,
) -> None:
    if json_output:
        typer.echo(json.dumps({"command": command, **result.to_dict()}))
        return
    if quiet:
        return
    console.print(result.message)
    if verbose:
        console.print(
            f"Diagnostics: storage_dir={result.storage_dir} "
            f"indexed_documents={result.indexed_documents} skipped_documents={result.skipped_documents}"
        )


def _emit_update_result(
    *,
    command: str,
    result: UpdateResult,
    json_output: bool,
    verbose: bool,
    quiet: bool,
) -> None:
    if json_output:
        typer.echo(json.dumps({"command": command, **result.to_dict()}))
        return
    if quiet:
        return
    console.print(result.message)
    if verbose:
        diff = result.diff
        console.print(
            f"Diagnostics: storage_dir={result.storage_dir} "
            f"manifest_path={result.manifest_path} "
            f"indexed_documents={result.indexed_documents} "
            f"skipped_documents={result.skipped_documents} "
            f"new={len(diff.new_paths)} "
            f"changed={len(diff.changed_paths)} "
            f"unchanged={len(diff.unchanged_paths)} "
            f"deleted={len(diff.deleted_paths)} "
            f"warnings={len(result.metadata_warnings)} "
            f"duplicate_groups={len(result.duplicate_groups)}"
        )


def _emit_query_result(
    *,
    result: QueryResult,
    cloud_llm_allowed: bool,
    json_output: bool,
    verbose: bool,
    quiet: bool,
) -> None:
    if json_output:
        typer.echo(json.dumps(result.to_dict()))
        return
    if quiet:
        return

    typer.echo("Antwort:")
    if result.answer:
        typer.echo(result.answer)
    else:
        typer.echo("Keine generierte Antwort verfügbar; Ausgabe basiert auf Retrieval und deterministischer Analyse.")

    typer.echo("Einschätzung:")
    if result.analysis.assessment:
        typer.echo(result.analysis.assessment)
    elif not result.llm_used:
        typer.echo("Retrieval-only mode; Bewertung basiert auf deterministischer Analyse.")
    else:
        typer.echo("Keine Einschätzung verfügbar.")

    typer.echo("Lösungsweg:")
    if result.analysis.solution_steps:
        for index, step in enumerate(result.analysis.solution_steps, start=1):
            typer.echo(f"{index}. {step}")
    else:
        typer.echo("Keine belastbaren Lösungsschritte verfügbar.")

    typer.echo(f"Routing: {result.analysis.routing.route} — {result.analysis.routing.rationale}")
    typer.echo(f"Confidence: {result.confidence.score}")
    typer.echo(f"Confidence rationale: {result.confidence.rationale}")

    typer.echo("Quellen:")
    for rank, source in enumerate(result.sources, start=1):
        typer.echo(f"{rank}. {source.path} (score={source.score}) — {source.excerpt}")

    typer.echo("Unsicherheiten:")
    if result.analysis.uncertainties:
        for uncertainty in result.analysis.uncertainties:
            typer.echo(f"- {uncertainty}")
    else:
        typer.echo("Keine expliziten Unsicherheiten.")

    typer.echo("Erkannte IDs:")
    if result.analysis.identifiers:
        for identifier in result.analysis.identifiers:
            typer.echo(f"{identifier.kind}: {identifier.value} (confidence={identifier.confidence}) — {identifier.evidence}")
    else:
        typer.echo("Keine.")

    typer.echo("Command Risks:")
    if result.analysis.command_risks:
        for risk in result.analysis.command_risks:
            typer.echo(f"{risk.risk} | {risk.command} | {risk.origin} | {risk.rationale}")
    else:
        typer.echo("Keine erkannt.")

    if verbose:
        diagnostics = result.retrieval_diagnostics
        graph = diagnostics.graph_retrieval
        graph_counts = ""
        if "document_count" in graph or "edge_count" in graph:
            graph_counts = f" graph_documents={graph.get('document_count', 'n/a')} graph_edges={graph.get('edge_count', 'n/a')}"
        typer.echo(
            f"Diagnostics: cloud_llm_allowed={cloud_llm_allowed} llm_used={result.llm_used} "
            f"status={result.status} source_count={len(result.sources)} "
            f"analysis_mode={result.analysis.mode} retrieval_backend={diagnostics.backend} "
            f"retrieval_strategy={diagnostics.strategy} graph_status={graph.get('status', 'unknown')} "
            f"graph_replacement={graph.get('replacement', 'n/a')}" + graph_counts
        )
        if diagnostics.score_components:
            typer.echo("Score components:")
            for component in diagnostics.score_components[:3]:
                data = component.to_dict()
                typer.echo(
                    f"- {data['path']} semantic={data['semantic_score']} lexical={data['lexical_score']} "
                    f"metadata={data['metadata_score']} graph={data['graph_score']} final={data['final_score']}"
                )


def _emit_status_result(*, result: IndexStatus, json_output: bool, quiet: bool) -> None:
    if json_output:
        typer.echo(json.dumps({"command": "status", **result.to_dict()}))
        return
    if quiet:
        return
    typer.echo(result.message)
    typer.echo(f"Status: {result.status}")
    typer.echo(f"Knowledge dir: {result.knowledge_dir}")
    typer.echo(f"Data dir: {result.data_dir}")
    typer.echo(f"Storage dir: {result.storage_dir}")
    typer.echo(f"Manifest: {result.manifest_path}")
    typer.echo(f"Vector index: {result.vector_index_path}")
    typer.echo(f"Documents: knowledge={result.knowledge_documents} indexed={result.indexed_documents}")
    typer.echo(f"Chunks: {result.chunks}")
    typer.echo(f"Storage files: {result.storage_files}")


def _emit_mock_corpus_result(
    *, command: str, result: MockCorpusResult, json_output: bool, quiet: bool
) -> None:
    if json_output:
        typer.echo(json.dumps({"command": command, **result.to_dict()}))
        return
    if quiet:
        return
    typer.echo(
        f"Generated {result.document_count} mock document(s) in {result.target_dir} "
        f"for dataset {result.dataset}."
    )
    typer.echo(f"Source types: {', '.join(result.source_types)}")


def _emit_mock_validation_result(
    *, result: MockValidationResult, json_output: bool, verbose: bool, quiet: bool
) -> None:
    if json_output:
        typer.echo(json.dumps({"command": "mock-validate", **result.to_dict()}))
        return
    if quiet:
        return
    status = "safe" if result.is_safe else "unsafe"
    typer.echo(f"Safety: {status}")
    typer.echo(f"Findings: {len(result.findings)}")
    for finding in result.findings[: 10 if verbose else 5]:
        typer.echo(f"- {finding.severity} {finding.code}: {finding.message} ({finding.path})")
    typer.echo("Coverage:")
    for name, counts in result.coverage.to_dict().items():
        rendered = ", ".join(f"{key}={value}" for key, value in counts.items()) or "none"
        typer.echo(f"{name}: {rendered}")


def _emit_quality_audit_result(
    *,
    result: KnowledgeQualityReport,
    report_path: Path | None,
    json_output: bool,
    verbose: bool,
    quiet: bool,
) -> None:
    payload = {"command": "quality-audit", **result.to_dict()}
    if report_path is not None:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    if json_output:
        typer.echo(json.dumps(payload, ensure_ascii=False))
        return
    if quiet:
        return
    typer.echo(f"Knowledge quality: documents={result.document_count} readiness_score={result.readiness_score}")
    weak = sorted(result.field_coverage.values(), key=lambda coverage: coverage.ratio)[:5]
    if weak:
        typer.echo("Weak dimensions:")
        for coverage in weak:
            typer.echo(f"- {coverage.field}: {coverage.present}/{coverage.total} ({coverage.ratio:.0%})")
    typer.echo("Recommendations:")
    for recommendation in result.recommendations[: 10 if verbose else 5]:
        scope = recommendation.path or "corpus"
        typer.echo(f"- {recommendation.severity} {scope}: {recommendation.suggestion}")
    if report_path is not None:
        typer.echo(f"Report written: {report_path}")


def _handle_error(error: Exception, *, verbose: bool) -> None:
    if verbose:
        raise error
    console.print(f"Configuration error: {error}", style="red", stderr=True)
    raise typer.Exit(code=1) from error


@app.command()
def index(
    json_output: JsonOption = False,
    verbose: VerboseOption = False,
    quiet: QuietOption = False,
    knowledge_dir: KnowledgeDirOption = None,
    data_dir: DataDirOption = None,
    storage_dir: StorageDirOption = None,
) -> None:
    """Build the initial knowledge index from Markdown files."""

    try:
        settings = _load_valid_settings(
            knowledge_dir=knowledge_dir,
            data_dir=data_dir,
            storage_dir=storage_dir,
            verbose=verbose,
            quiet=quiet,
        )
        result = RagEngine(settings).index_markdown()
    except Exception as error:
        _handle_error(error, verbose=verbose)
    _emit_index_result(
        command="index",
        result=result,
        json_output=json_output,
        verbose=verbose,
        quiet=quiet,
    )


@app.command()
def update(
    json_output: JsonOption = False,
    verbose: VerboseOption = False,
    quiet: QuietOption = False,
    knowledge_dir: KnowledgeDirOption = None,
    data_dir: DataDirOption = None,
    storage_dir: StorageDirOption = None,
) -> None:
    """Incrementally update the knowledge index from new and changed Markdown files."""

    try:
        settings = _load_valid_settings(
            knowledge_dir=knowledge_dir,
            data_dir=data_dir,
            storage_dir=storage_dir,
            verbose=verbose,
            quiet=quiet,
        )
        result = RagEngine(settings).update_markdown()
    except Exception as error:
        _handle_error(error, verbose=verbose)
    _emit_update_result(
        command="update",
        result=result,
        json_output=json_output,
        verbose=verbose,
        quiet=quiet,
    )


@app.command()
def query(
    ticket_text: str,
    json_output: JsonOption = False,
    verbose: VerboseOption = False,
    quiet: QuietOption = False,
    knowledge_dir: KnowledgeDirOption = None,
    data_dir: DataDirOption = None,
    storage_dir: StorageDirOption = None,
) -> None:
    """Query the knowledge base with ticket text."""

    try:
        settings = _load_valid_settings(
            knowledge_dir=knowledge_dir,
            data_dir=data_dir,
            storage_dir=storage_dir,
            verbose=verbose,
            quiet=quiet,
        )
        result = RagEngine(settings).query(ticket_text)
    except IndexMissingError as error:
        typer.echo(str(error), err=True)
        raise typer.Exit(code=1) from error
    except Exception as error:
        _handle_error(error, verbose=verbose)
    _emit_query_result(
        result=result,
        cloud_llm_allowed=settings.can_use_cloud_llm,
        json_output=json_output,
        verbose=verbose,
        quiet=quiet,
    )


@app.command()
def status(
    json_output: JsonOption = False,
    quiet: QuietOption = False,
    knowledge_dir: KnowledgeDirOption = None,
    data_dir: DataDirOption = None,
    storage_dir: StorageDirOption = None,
) -> None:
    """Show configured paths and local index counts."""

    try:
        settings = _load_valid_settings(
            knowledge_dir=knowledge_dir,
            data_dir=data_dir,
            storage_dir=storage_dir,
            quiet=quiet,
        )
        result = RagEngine(settings).status()
    except Exception as error:
        _handle_error(error, verbose=False)
    _emit_status_result(result=result, json_output=json_output, quiet=quiet)


@app.command()
def reindex(
    json_output: JsonOption = False,
    verbose: VerboseOption = False,
    quiet: QuietOption = False,
    knowledge_dir: KnowledgeDirOption = None,
    data_dir: DataDirOption = None,
    storage_dir: StorageDirOption = None,
) -> None:
    """Rebuild the knowledge index from scratch."""

    try:
        settings = _load_valid_settings(
            knowledge_dir=knowledge_dir,
            data_dir=data_dir,
            storage_dir=storage_dir,
            verbose=verbose,
            quiet=quiet,
        )
        result = RagEngine(settings).reindex_markdown()
    except Exception as error:
        _handle_error(error, verbose=verbose)
    _emit_index_result(
        command="reindex",
        result=result,
        json_output=json_output,
        verbose=verbose,
        quiet=quiet,
    )


@app.command("mock-init")
def mock_init(
    target_dir: MockTargetDirOption = Path("knowledge/mock/v1"),
    dataset: Annotated[str, typer.Option("--dataset", help="Mock dataset name to write into frontmatter.")] = "mock-v1",
    json_output: JsonOption = False,
    quiet: QuietOption = False,
) -> None:
    """Generate a deterministic synthetic mock corpus."""

    result = generate_mock_corpus(target_dir, dataset=dataset)
    _emit_mock_corpus_result(command="mock-init", result=result, json_output=json_output, quiet=quiet)


@app.command("mock-validate")
def mock_validate(
    corpus_dir: MockCorpusDirOption = Path("knowledge/mock/v1"),
    json_output: JsonOption = False,
    verbose: VerboseOption = False,
    quiet: QuietOption = False,
) -> None:
    """Validate mock corpus safety markers and coverage."""

    result = validate_mock_corpus(corpus_dir)
    _emit_mock_validation_result(result=result, json_output=json_output, verbose=verbose, quiet=quiet)


@app.command("quality-audit")
def quality_audit(
    corpus_dir: QualityCorpusDirOption = Path("/Users/timo/obsidian/secondBrain/Arbeit/06_OOD-KB/articles"),
    expected_documents: Annotated[int | None, typer.Option("--expected-documents", help="Expected Markdown document count.")] = 438,
    report_path: Annotated[Path | None, typer.Option("--report-path", help="Optional local JSON report path.")] = None,
    json_output: JsonOption = False,
    quiet: QuietOption = False,
    verbose: VerboseOption = False,
) -> None:
    """Audit a Markdown corpus for retrieval-readiness quality signals."""

    result = audit_knowledge_corpus(corpus_dir, expected_documents=expected_documents)
    _emit_quality_audit_result(
        result=result,
        report_path=report_path,
        json_output=json_output,
        verbose=verbose,
        quiet=quiet,
    )


__all__ = ["app"]


# Deferred import — must stay at the bottom of cli.py so all helpers and
# option types referenced by ood.eval_cli (DataDirOption, JsonOption,
# KnowledgeDirOption, QuietOption, StorageDirOption, VerboseOption,
# _handle_error, _load_valid_settings) are already defined by the time the
# reverse-direction import triggers re-entry into this module.
from ood.eval_cli import eval_app  # noqa: E402  (deferred to avoid circular import)

app.add_typer(eval_app, name="eval")
