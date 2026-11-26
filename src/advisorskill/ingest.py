"""Import feedback without interpreting its content."""

import hashlib
import json
import unicodedata
from pathlib import Path

from advisorskill.models import Feedback, FeedbackInput, WorkspaceState
from advisorskill.serialization import read_yaml
from advisorskill.storage import AdvisorError, parse_record, unique_object

CONTENT_FIELDS = (
    "comment", "context_before", "context_after", "scope", "section", "thread_ref", "author_role",
)
MARKDOWN_FIELDS = {
    "### Context before": "context_before",
    "### Context after": "context_after",
    "### Metadata": "metadata",
}


def normalize(value: str | None):
    if value is None:
        return None
    return unicodedata.normalize("NFC", value.replace("\r\n", "\n").replace("\r", "\n")).strip()


def content_id(record: FeedbackInput):
    source_ref = normalize(record.source_ref)
    revision = normalize(record.revision)
    if record.supersedes is not None:
        identity = ["context-correction", record.supersedes]
    elif source_ref is not None and revision is not None:
        identity = ["source-revision", record.source, source_ref, revision]
    else:
        content = [normalize(getattr(record, field)) for field in CONTENT_FIELDS]
        identity = ["content", record.source, source_ref, revision, content]
    encoded = json.dumps(identity, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return "fb-" + hashlib.sha256(encoded).hexdigest()


def jsonl_records(text: str):
    for line_number, line in enumerate(text.split("\n"), 1):
        if not line.strip():
            continue
        label = f"JSONL line {line_number}"
        try:
            data = json.loads(line, object_pairs_hook=unique_object)
        except (ValueError, RecursionError):
            raise AdvisorError(f"{label} is invalid JSON.") from None
        yield parse_record(FeedbackInput, data, label)


def markdown_record(fields: dict[str, list[str]], line_number: int):
    label = f"Markdown feedback at line {line_number}"
    data = {key: "\n".join(value).strip() for key, value in fields.items()}
    if "metadata" in data:
        metadata = read_yaml(data.pop("metadata"), label)
        if not isinstance(metadata, dict) or metadata.keys() & {"comment", *MARKDOWN_FIELDS.values()}:
            raise AdvisorError(f"{label} must use a metadata mapping with metadata fields only.")
        data.update(metadata)
    return parse_record(FeedbackInput, data, label)


def markdown_records(text: str):
    fields = None
    for line_number, line in enumerate(text.split("\n"), 1):
        if line.rstrip() == "## Feedback":
            if fields is not None:
                yield markdown_record(fields, start)
            start, name, fields = line_number, "comment", {"comment": []}
        elif fields is not None:
            if line.rstrip() in MARKDOWN_FIELDS:
                name = MARKDOWN_FIELDS[line.rstrip()]
                if name in fields:
                    raise AdvisorError(f"Duplicate Markdown field at line {line_number}.")
                fields[name] = []
            else:
                fields[name].append(line)
        elif line.strip() and not line.startswith("# "):
            raise AdvisorError(f"Expected a Markdown feedback marker at line {line_number}.")
    if fields is not None:
        yield markdown_record(fields, start)


def equivalent(left: Feedback, right: Feedback):
    return all(
        normalize(value) == normalize(getattr(right, name)) if isinstance(value, str)
        else value == getattr(right, name)
        for name, value in left.model_dump().items()
    )


def check_correction(record, previous_records, superseded):
    target = record.supersedes
    if target is None:
        return
    prior = previous_records.get(target)
    if prior is None or target in superseded:
        raise AdvisorError("A correction must reference a current feedback record in this workspace.")
    provenance = ("source", "source_ref", "revision", "comment")
    if any(getattr(record, key) != getattr(prior, key) for key in provenance):
        raise AdvisorError("A context correction must preserve source identity and comment wording.")
    superseded.add(target)


def ingest_file(state: WorkspaceState, path: Path):
    parsers = {".jsonl": jsonl_records, ".md": markdown_records, ".markdown": markdown_records}
    parser = parsers.get(path.suffix.lower())
    if parser is None:
        raise AdvisorError("Input must use .jsonl, .md or .markdown.")
    existing = {record.id: record for record in state.feedback}
    superseded = {record.supersedes for record in state.feedback if record.supersedes}
    added = duplicates = 0
    for item in parser(path.read_text(encoding="utf-8-sig")):
        record = Feedback(id=content_id(item), **item.model_dump())
        previous = existing.get(record.id)
        if previous is None:
            check_correction(record, existing, superseded)
            existing[record.id] = record
            added += 1
        elif equivalent(previous, record):
            duplicates += 1
        else:
            raise AdvisorError(f"Feedback {record.id} differs from the stored source revision.")
    if not added and not duplicates:
        raise AdvisorError("Input contained no feedback records.")
    return state.model_copy(update={"feedback": tuple(existing.values())}), added, duplicates
