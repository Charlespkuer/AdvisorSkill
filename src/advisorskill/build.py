"""Render approved writing rules into a deterministic local Agent Skill."""

import hashlib
import json
import tempfile
from pathlib import Path

from advisorskill.models import Category, Rule, WorkspaceState
from advisorskill.storage import AdvisorError, is_redirect, json_text, resolve_path, unique_object, writer_lock

MANIFEST = ".advisorskill-build.json"
ALLOWED_FILES = {"SKILL.md", *(f"references/{item.value}.md" for item in Category)}


def markdown_text(text: str):
    # Keep user-authored rule text within its Markdown paragraph or list item.
    return "".join(
        f"&#{ord(char)};" if char in "&<>`[]*!_\\#~" else char
        for char in " ".join(text.split())
    )


def render_rule(rule: Rule, *, heading_level: int = 2):
    lines = [
        f"{'#' * heading_level} {rule.id}",
        "",
        markdown_text(rule.statement),
        "",
        f"- Scope: {rule.scope.level}",
        f"- Confidence: {rule.confidence}",
    ]
    for heading, items in (
        ("Sections", rule.scope.sections),
        ("Conditions", rule.scope.conditions),
        ("Exceptions", rule.scope.exceptions),
    ):
        if items:
            lines.extend((f"- {heading}:", *(f"  - {markdown_text(item)}" for item in items)))
    return "\n".join(lines)


def render_skill(state: WorkspaceState):
    name = f"advisor-{state.profile.profile_id}"
    files = {}
    index = []
    for category in Category:
        rules = sorted(
            (rule for rule in state.rules if rule.status == "active" and rule.category == category),
            key=lambda rule: rule.id,
        )
        if rules:
            title = category.value.replace("_", " ").title()
            path = f"references/{category.value}.md"
            files[path] = f"# {title}\n\n" + "\n\n".join(map(render_rule, rules)) + "\n"
            index.append(f"- [{title}]({path})")

    links = "\n".join(index) if index else "This profile currently has no active rules."
    files["SKILL.md"] = f"""---
name: {name}
description: Applies reviewed advisor writing preferences when diagnosing or revising an academic manuscript for this profile.
---

# Advisor writing preferences

Use this skill when the author explicitly selects this profile for a manuscript review or revision.

1. Confirm the scientific argument, the author's current request, and target venue when available.
2. Read the relevant topic files below. Check each rule's scope, conditions, and exceptions before applying it.
3. Diagnose before editing. For each change, show the original, the suggestion, the reason, and the rule ID.
4. Preserve scientific facts, results, mathematical conclusions, and citations. Follow verified venue requirements and the author's current instructions over general preferences. Explain conflicts before applying edits.
5. Attribute suggestions to this profile's reviewed rules. Avoid implying that an advisor personally reviewed or endorsed the manuscript.

## Topic references

{links}
"""
    return files


def fingerprint(data: bytes):
    return hashlib.sha256(data).hexdigest()


def check_owned(directory: Path):
    """Return the build's checksums if it contains only unmodified generated files."""
    error = AdvisorError("Existing build directory contains unrecognized or modified content.")
    if is_redirect(directory) or not directory.is_dir():
        raise error
    manifest = directory / MANIFEST
    if is_redirect(manifest) or not manifest.is_file():
        raise error
    try:
        checksums = json.loads(manifest.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
    except (UnicodeError, ValueError, RecursionError):
        raise error from None
    if not isinstance(checksums, dict) or "SKILL.md" not in checksums:
        raise error
    if not checksums.keys() <= ALLOWED_FILES:
        raise error
    expected = {MANIFEST, "SKILL.md"}
    references = {item.removeprefix("references/") for item in checksums if item.startswith("references/")}
    if references:
        expected.add("references")
    if {item.name for item in directory.iterdir()} != expected:
        raise error
    if references:
        path = directory / "references"
        if is_redirect(path) or not path.is_dir() or {item.name for item in path.iterdir()} != references:
            raise error
    for filename, checksum in checksums.items():
        path = directory / filename
        if is_redirect(path) or not path.is_file() or fingerprint(path.read_bytes()) != checksum:
            raise error
    return checksums


def build_skill(state: WorkspaceState, workspace: Path, output: Path):
    name = f"advisor-{state.profile.profile_id}"
    target = output / name
    previous = output / f".{name}.previous"
    for path in (target, previous):
        if is_redirect(path):
            raise AdvisorError("Build paths must not redirect.")
        resolved = resolve_path(path)
        if resolved == workspace or resolved in workspace.parents:
            raise AdvisorError("Build paths must not redirect or contain the private workspace.")

    files = render_skill(state)
    payload = {filename: text.encode("utf-8") for filename, text in files.items()}
    checksums = {filename: fingerprint(data) for filename, data in payload.items()}

    output.mkdir(parents=True, exist_ok=True)
    with writer_lock(output, f".{name}.lock"):
        if previous.exists():
            check_owned(previous)
            if target.exists():
                check_owned(target)
                with tempfile.TemporaryDirectory(prefix=".build-", dir=output) as scratch:
                    previous.rename(Path(scratch) / "retired")
            else:
                previous.rename(target)

        old_checksums = check_owned(target) if target.exists() else None
        if old_checksums == checksums:
            return name
        with tempfile.TemporaryDirectory(prefix=".build-", dir=output) as scratch:
            staged = Path(scratch) / name
            for filename, data in payload.items():
                path = staged / filename
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
            (staged / MANIFEST).write_bytes(json_text(checksums).encode("utf-8"))

            if old_checksums is not None:
                target.rename(previous)
            try:
                staged.rename(target)
            except OSError:
                if old_checksums is not None:
                    previous.rename(target)
                raise

            if old_checksums is not None:
                previous.rename(Path(scratch) / "retired")
    return name
