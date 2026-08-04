"""Extract short key-figure digests from CSV/JSON open-data payloads for LLM cards."""

from __future__ import annotations

import csv
import io
import json
import re
from collections.abc import Mapping, Sequence
from typing import Any

_EDITOR_NOTES: str = (
    "EDITOR NOTES (open dataset, not a news article):\n"
    "- Prefer concrete figures from \"Key figures\" in one_sentence_summary and "
    "plain_language.\n"
    "- Do not invent numbers that are not listed below.\n"
    "- Explain briefly what the dataset means for residents of Germany."
)

_MAX_COLUMNS_LISTED: int = 12
_MAX_NUMERIC_COLUMNS: int = 4
_MAX_PREVIEW_ROWS: int = 6
_MAX_ROWS_SCAN: int = 4000
_BOM: str = "\ufeff"


def build_tabular_digest(
    text: str,
    *,
    max_preview_rows: int = _MAX_PREVIEW_ROWS,
    max_digest_chars: int = 2500,
) -> str:
    """Return a compact English digest of tabular/JSON content, or empty string."""
    stripped: str = text.lstrip(_BOM).strip()
    if not stripped:
        return ""

    digest: str = ""
    if _looks_like_json(stripped):
        digest = _digest_json(stripped, max_preview_rows=max_preview_rows)
    if not digest:
        digest = _digest_csv(stripped, max_preview_rows=max_preview_rows)
    if not digest:
        return ""
    if len(digest) > max_digest_chars:
        return f"{digest[: max_digest_chars - 1]}…"
    return digest


def build_open_dataset_summary(
    *,
    title: str,
    dataset_uri: str,
    resource_uri: str,
    publisher: str,
    licence_name: str,
    licence_uri: str,
    body_text: str,
    max_body_chars: int,
    extra_meta_lines: Sequence[str] = (),
) -> str:
    """Build raw_item.summary: editor notes + metadata + key figures + truncated body."""
    digest: str = build_tabular_digest(body_text)
    truncated_body: str = body_text
    if len(truncated_body) > max_body_chars:
        truncated_body = f"{truncated_body[:max_body_chars]}…"

    meta_lines: list[str] = [
        f"Dataset: {title}",
        f"Dataset URI: {dataset_uri}",
        f"Resource URI: {resource_uri}",
        f"Publisher: {publisher}",
        f"License: {licence_name or 'unknown'}",
        f"License URI: {licence_uri or 'n/a'}",
    ]
    for line in extra_meta_lines:
        cleaned: str = line.strip()
        if cleaned:
            meta_lines.append(cleaned)

    parts: list[str] = [_EDITOR_NOTES, "", *meta_lines, ""]
    if digest:
        parts.extend([digest, ""])
    parts.append(truncated_body)
    return "\n".join(parts)


def is_open_dataset_summary(summary: str) -> bool:
    """True when summary was built for an open government dataset."""
    return "EDITOR NOTES (open dataset" in summary or "Dataset URI:" in summary


def ensure_open_dataset_key_figures(summary: str) -> str:
    """Insert Key figures into older open-data summaries that lack a digest."""
    if "Key figures (extracted" in summary:
        return summary
    if not is_open_dataset_summary(summary) and not summary.lstrip().startswith("Dataset:"):
        return summary
    parts: list[str] = summary.split("\n\n")
    body: str = parts[-1] if parts else summary
    digest: str = build_tabular_digest(body)
    if not digest:
        digest = build_tabular_digest(summary)
    if not digest:
        return summary
    if len(parts) >= 2:
        return "\n\n".join([*parts[:-1], digest, parts[-1]])
    return f"{digest}\n\n{summary}"


def _looks_like_json(text: str) -> bool:
    head: str = text.lstrip()[:1]
    return head in {"{", "["}


def _digest_json(text: str, *, max_preview_rows: int) -> str:
    try:
        payload: object = json.loads(text)
    except (json.JSONDecodeError, UnicodeError, ValueError):
        return ""

    if isinstance(payload, list) and payload and all(isinstance(item, Mapping) for item in payload):
        rows: list[dict[str, str]] = [_stringify_row(item) for item in payload[:_MAX_ROWS_SCAN]]
        if not rows:
            return ""
        columns: list[str] = list(rows[0].keys())
        for row in rows[1:]:
            for key in row:
                if key not in columns:
                    columns.append(key)
        return _format_table_digest(
            columns=columns,
            rows=rows,
            row_count_hint=len(payload) if isinstance(payload, list) else len(rows),
            max_preview_rows=max_preview_rows,
            source_label="JSON array of objects",
        )

    if isinstance(payload, Mapping):
        keys: list[str] = [str(key) for key in list(payload.keys())[:_MAX_COLUMNS_LISTED]]
        sample: str = json.dumps(payload, ensure_ascii=False)[:800]
        lines: list[str] = [
            "Key figures (extracted from JSON object):",
            f"- Top-level keys: {', '.join(keys) if keys else '(none)'}",
            f"- Sample: {sample}{'…' if len(sample) >= 800 else ''}",
        ]
        return "\n".join(lines)
    return ""


def _stringify_row(item: Mapping[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    for key, value in item.items():
        if value is None:
            out[str(key)] = ""
        elif isinstance(value, (str, int, float, bool)):
            out[str(key)] = str(value)
        else:
            out[str(key)] = json.dumps(value, ensure_ascii=False)
    return out


def _digest_csv(text: str, *, max_preview_rows: int) -> str:
    delimiter: str | None = _detect_delimiter(text)
    if delimiter is None:
        return ""
    try:
        reader: csv.DictReader[str] = csv.DictReader(io.StringIO(text), delimiter=delimiter)
        if not reader.fieldnames:
            return ""
        columns: list[str] = [name.strip() for name in reader.fieldnames if name and name.strip()]
        if not columns:
            return ""
        rows: list[dict[str, str]] = []
        for raw_row in reader:
            if len(rows) >= _MAX_ROWS_SCAN:
                break
            if not isinstance(raw_row, dict):
                continue
            normalized: dict[str, str] = {}
            empty: bool = True
            for col in columns:
                value: str = str(raw_row.get(col) or "").strip()
                normalized[col] = value
                if value:
                    empty = False
            if not empty:
                rows.append(normalized)
    except csv.Error:
        return ""

    if not rows:
        return ""
    return _format_table_digest(
        columns=columns,
        rows=rows,
        row_count_hint=len(rows),
        max_preview_rows=max_preview_rows,
        source_label=f"CSV (delimiter {delimiter!r})",
    )


def _detect_delimiter(text: str) -> str | None:
    sample: str = "\n".join(text.splitlines()[:20])
    if not sample.strip():
        return None
    try:
        dialect: csv.Dialect = csv.Sniffer().sniff(sample, delimiters=";,|\t,")
        if dialect.delimiter:
            return dialect.delimiter
    except csv.Error:
        pass
    first_line: str = text.splitlines()[0] if text.splitlines() else ""
    for candidate in (";", ",", "\t", "|"):
        if candidate in first_line:
            return candidate
    return None


def _format_table_digest(
    *,
    columns: Sequence[str],
    rows: Sequence[Mapping[str, str]],
    row_count_hint: int,
    max_preview_rows: int,
    source_label: str,
) -> str:
    shown_columns: Sequence[str] = columns[:_MAX_COLUMNS_LISTED]
    col_note: str = ""
    if len(columns) > _MAX_COLUMNS_LISTED:
        col_note = f" (+{len(columns) - _MAX_COLUMNS_LISTED} more)"

    lines: list[str] = [
        "Key figures (extracted from tabular data):",
        f"- Format: {source_label}",
        f"- Columns: {', '.join(shown_columns)}{col_note}",
        f"- Rows in sample: {row_count_hint}",
    ]

    preview: list[Mapping[str, str]] = _pick_preview_rows(rows, max_preview_rows)
    if preview:
        lines.append("- Preview rows:")
        for row in preview:
            cells: list[str] = [row.get(col, "") for col in shown_columns[:6]]
            lines.append(f"  • {' | '.join(cells)}")

    numeric_notes: list[str] = _numeric_column_notes(columns, rows)
    if numeric_notes:
        lines.append("- Numeric highlights:")
        lines.extend(f"  • {note}" for note in numeric_notes)

    return "\n".join(lines)


def _pick_preview_rows(
    rows: Sequence[Mapping[str, str]],
    max_preview_rows: int,
) -> list[Mapping[str, str]]:
    if max_preview_rows <= 0 or not rows:
        return []
    if len(rows) <= max_preview_rows:
        return list(rows)
    head: int = max(1, max_preview_rows // 3)
    tail: int = max_preview_rows - head
    return [*rows[:head], *rows[-tail:]]


def _numeric_column_notes(
    columns: Sequence[str],
    rows: Sequence[Mapping[str, str]],
) -> list[str]:
    notes: list[str] = []
    for col in columns:
        values: list[float] = []
        for row in rows:
            parsed: float | None = parse_number(row.get(col, ""))
            if parsed is not None:
                values.append(parsed)
        if len(values) < 2:
            if len(values) == 1:
                notes.append(f"{col}: last={format_number(values[-1])}")
            continue
        last: float = values[-1]
        prev: float = values[-2]
        delta: float = last - prev
        note: str = f"{col}: last={format_number(last)}, previous={format_number(prev)}, change={format_number(delta)}"
        if prev != 0:
            pct: float = (delta / abs(prev)) * 100.0
            note = f"{note} ({format_number(pct)}%)"
        notes.append(note)
        if len(notes) >= _MAX_NUMERIC_COLUMNS:
            break
    return notes


_NUMBER_RE: re.Pattern[str] = re.compile(r"^[\s\-+]?\d[\d.\s\u00a0,]*$")


def parse_number(raw: str) -> float | None:
    """Parse DE/EN numeric cell; return None when not a plain number."""
    s: str = raw.strip().replace("\xa0", "").replace(" ", "")
    if not s or not _NUMBER_RE.match(s):
        return None
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        left, _, right = s.partition(",")
        if right.isdigit() and len(right) <= 3 and left.replace("-", "").isdigit():
            s = f"{left}.{right}"
        else:
            s = s.replace(",", "")
    try:
        return float(s)
    except ValueError:
        return None


def format_number(value: float) -> str:
    """Compact number formatting for digest lines."""
    if abs(value - round(value)) < 1e-9:
        return f"{int(round(value)):,}".replace(",", " ")
    rendered: str = f"{value:.4f}".rstrip("0").rstrip(".")
    return rendered
