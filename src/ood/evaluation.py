from __future__ import annotations

import json
from dataclasses import dataclass
from json import JSONDecodeError
from pathlib import Path, PurePosixPath
from typing import Any


SUPPORTED_SCHEMA_VERSION = 1


class EvaluationDatasetError(ValueError):
    """Raised when an evaluation dataset cannot be loaded safely."""


@dataclass(frozen=True)
class ExpectedIdentifier:
    kind: str
    value: str


@dataclass(frozen=True)
class ExpectedCommandRisk:
    command_contains: str
    risk: str


@dataclass(frozen=True)
class EvaluationCase:
    id: str
    query: str
    expected_sources: tuple[str, ...]
    forbidden_sources: tuple[str, ...]
    expected_intent: str
    expected_route: str
    expected_identifiers: tuple[ExpectedIdentifier, ...]
    expected_command_risks: tuple[ExpectedCommandRisk, ...]
    expected_uncertainties: tuple[str, ...]
    expected_llm_answer: str | None = None


@dataclass(frozen=True)
class EvaluationDataset:
    schema_version: int
    dataset: str
    cases: tuple[EvaluationCase, ...]


def load_evaluation_dataset(path: Path, *, knowledge_dir: Path | None = None) -> EvaluationDataset:
    """Load and validate a versioned OOD evaluation dataset JSON file."""

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except JSONDecodeError as exc:
        raise EvaluationDatasetError(f"Malformed JSON in evaluation dataset {path}: {exc.msg}") from exc

    if not isinstance(raw, dict):
        raise EvaluationDatasetError("Evaluation dataset must be a JSON object.")

    schema_version = raw.get("schema_version")
    if schema_version != SUPPORTED_SCHEMA_VERSION:
        raise EvaluationDatasetError(
            f"Unsupported schema_version {schema_version!r}; expected {SUPPORTED_SCHEMA_VERSION}."
        )

    dataset_name = _required_str(raw, "dataset", context="dataset")
    raw_cases = raw.get("cases")
    if not isinstance(raw_cases, list):
        raise EvaluationDatasetError("dataset.cases must be a list.")

    seen_ids: set[str] = set()
    cases: list[EvaluationCase] = []
    for index, raw_case in enumerate(raw_cases):
        if not isinstance(raw_case, dict):
            raise EvaluationDatasetError(f"cases[{index}] must be an object.")
        case = _parse_case(raw_case, index=index)
        if case.id in seen_ids:
            raise EvaluationDatasetError(f"Duplicate case id {case.id!r}.")
        seen_ids.add(case.id)
        cases.append(case)

    if knowledge_dir is not None:
        _validate_source_references(cases, knowledge_dir)

    return EvaluationDataset(
        schema_version=schema_version,
        dataset=dataset_name,
        cases=tuple(cases),
    )


def _parse_case(raw_case: dict[str, Any], *, index: int) -> EvaluationCase:
    context = f"cases[{index}]"
    case_id = _required_str(raw_case, "id", context=context)
    query = _required_str(raw_case, "query", context=context)
    expected_sources = _required_source_tuple(raw_case, "expected_sources", context=context)
    if not expected_sources:
        raise EvaluationDatasetError(f"{context}.expected_sources must contain at least one path.")

    return EvaluationCase(
        id=case_id,
        query=query,
        expected_sources=expected_sources,
        forbidden_sources=_required_source_tuple(raw_case, "forbidden_sources", context=context),
        expected_intent=_required_str(raw_case, "expected_intent", context=context),
        expected_route=_required_str(raw_case, "expected_route", context=context),
        expected_identifiers=_parse_expected_identifiers(raw_case, context=context),
        expected_command_risks=_parse_expected_command_risks(raw_case, context=context),
        expected_uncertainties=_required_str_tuple(raw_case, "expected_uncertainties", context=context),
        expected_llm_answer=_optional_str(raw_case, "expected_llm_answer", context=context),
    )


def _required_str(raw: dict[str, Any], field: str, *, context: str) -> str:
    value = raw.get(field)
    if not isinstance(value, str) or not value.strip():
        raise EvaluationDatasetError(f"{context}.{field} must be a non-empty string.")
    return value.strip()


def _optional_str(raw: dict[str, Any], field: str, *, context: str) -> str | None:
    if field not in raw or raw[field] is None:
        return None
    value = raw[field]
    if not isinstance(value, str) or not value.strip():
        raise EvaluationDatasetError(
            f"{context}.{field} must be a non-empty string when present."
        )
    return value.strip()


def _required_str_tuple(raw: dict[str, Any], field: str, *, context: str) -> tuple[str, ...]:
    value = raw.get(field)
    if not isinstance(value, list):
        raise EvaluationDatasetError(f"{context}.{field} must be a list of strings.")
    strings: list[str] = []
    for item_index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise EvaluationDatasetError(
                f"{context}.{field}[{item_index}] must be a non-empty string."
            )
        strings.append(item.strip())
    return tuple(strings)


def _required_source_tuple(raw: dict[str, Any], field: str, *, context: str) -> tuple[str, ...]:
    return tuple(_normalize_source_path(path, field=f"{context}.{field}") for path in _required_str_tuple(raw, field, context=context))


def _normalize_source_path(path: str, *, field: str) -> str:
    posix = path.replace("\\", "/")
    pure_path = PurePosixPath(posix)
    if pure_path.is_absolute():
        raise EvaluationDatasetError(f"{field} paths must be relative, got {path!r}.")
    parts = pure_path.parts
    if ".." in parts:
        raise EvaluationDatasetError(f"{field} paths must not use traversal, got {path!r}.")
    normalized = pure_path.as_posix().removeprefix("./")
    if not normalized or normalized == ".":
        raise EvaluationDatasetError(f"{field} paths must be non-empty relative paths.")
    return normalized


def _parse_expected_identifiers(
    raw_case: dict[str, Any], *, context: str
) -> tuple[ExpectedIdentifier, ...]:
    raw_items = raw_case.get("expected_identifiers")
    if not isinstance(raw_items, list):
        raise EvaluationDatasetError(f"{context}.expected_identifiers must be a list.")
    identifiers: list[ExpectedIdentifier] = []
    for item_index, raw_item in enumerate(raw_items):
        item_context = f"{context}.expected_identifiers[{item_index}]"
        if not isinstance(raw_item, dict):
            raise EvaluationDatasetError(f"{item_context} must be an object.")
        identifiers.append(
            ExpectedIdentifier(
                kind=_required_str(raw_item, "kind", context=item_context),
                value=_required_str(raw_item, "value", context=item_context),
            )
        )
    return tuple(identifiers)


def _parse_expected_command_risks(
    raw_case: dict[str, Any], *, context: str
) -> tuple[ExpectedCommandRisk, ...]:
    raw_items = raw_case.get("expected_command_risks")
    if not isinstance(raw_items, list):
        raise EvaluationDatasetError(f"{context}.expected_command_risks must be a list.")
    risks: list[ExpectedCommandRisk] = []
    for item_index, raw_item in enumerate(raw_items):
        item_context = f"{context}.expected_command_risks[{item_index}]"
        if not isinstance(raw_item, dict):
            raise EvaluationDatasetError(f"{item_context} must be an object.")
        risks.append(
            ExpectedCommandRisk(
                command_contains=_required_str(raw_item, "command_contains", context=item_context),
                risk=_required_str(raw_item, "risk", context=item_context),
            )
        )
    return tuple(risks)


def _validate_source_references(cases: list[EvaluationCase], knowledge_dir: Path) -> None:
    missing: list[str] = []
    for case in cases:
        for source_path in (*case.expected_sources, *case.forbidden_sources):
            if not (knowledge_dir / source_path).is_file():
                missing.append(source_path)
    if missing:
        unique_missing = sorted(set(missing))
        raise EvaluationDatasetError(
            "Evaluation dataset references missing knowledge source paths: "
            + ", ".join(unique_missing)
        )


__all__ = [
    "EvaluationCase",
    "EvaluationDataset",
    "EvaluationDatasetError",
    "ExpectedCommandRisk",
    "ExpectedIdentifier",
    "load_evaluation_dataset",
]
