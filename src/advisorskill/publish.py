"""Draft, submit, and curate the single public guide for an advisor."""

import hashlib
import re
import subprocess
import tempfile
from itertools import groupby
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

import yaml

from advisorskill.build import render_rule
from advisorskill.models import ProfileID, Record, WorkspaceState
from advisorskill.serialization import read_yaml
from advisorskill.storage import AdvisorError, atomic_write, is_redirect, parse_record, writer_lock

REPOSITORY = "Charlespkuer/AdvisorSkill"
GUIDE_NAME = "GUIDE.md"
LICENSES = ("CC0-1.0", "CC-BY-4.0", "CC-BY-SA-4.0")


class PublicGuide(Record):
    format: Literal["advisorskill-guide-v1"]
    discipline: ProfileID
    advisor: ProfileID
    license: Literal["CC0-1.0", "CC-BY-4.0", "CC-BY-SA-4.0"]

    @property
    def key(self):
        return f"{self.discipline}/{self.advisor}"


def public_guide(text: str):
    start, separator, body = text.partition("\n---\n")
    if not text.startswith("---\n") or not separator or not body.strip():
        raise AdvisorError("A public guide needs AdvisorSkill front matter and a Markdown body.")
    if len(text.encode("utf-8")) > 55_000:
        raise AdvisorError("A public guide must fit within 55 KB. Submit a smaller set of rules.")
    return parse_record(PublicGuide, read_yaml(start[4:], "Guide metadata"), "Public guide")


def render_public(state: WorkspaceState, args):
    metadata = parse_record(PublicGuide, {
        "format": "advisorskill-guide-v1",
        "discipline": args.discipline,
        "advisor": args.advisor,
        "license": args.license,
    }, "Public guide")
    active = {rule.id: rule for rule in state.rules if rule.status == "active"}
    if not set(args.rule).issubset(active):
        raise AdvisorError("Each selected rule must be active and approved.")
    selected = sorted((active[item] for item in set(args.rule)), key=lambda rule: (rule.category, rule.id))
    # Only the reviewed rule fields used by render_rule enter this document.
    sections = []
    for category, rules in groupby(selected, key=lambda rule: rule.category):
        title = category.value.replace("_", " ").title()
        sections.append(f"## {title}\n\n" + "\n\n".join(
            render_rule(rule, heading_level=3) for rule in rules
        ))
    body = "\n\n".join(sections)
    front_matter = yaml.safe_dump(metadata.model_dump(), sort_keys=False)
    text = f"---\n{front_matter}---\n\n# Writing guide for {metadata.key}\n\n{body}\n"
    public_guide(text)
    return metadata, text


def guide_path(root: Path, metadata: PublicGuide):
    directory = root
    for segment in (metadata.discipline, metadata.advisor):
        directory /= segment
        if is_redirect(directory):
            raise AdvisorError("Guide directories must not redirect.")
    target = directory / GUIDE_NAME
    if is_redirect(target):
        raise AdvisorError("The guide file must not redirect.")
    return target


def write_guide(root: Path, metadata: PublicGuide, text: str, *, replace=False):
    root.mkdir(parents=True, exist_ok=True)
    with writer_lock(root):
        target = guide_path(root, metadata)
        if target.exists():
            if read_guide(target)[1] == text:
                return
            if not replace:
                raise AdvisorError("A different guide exists. Review and merge the changes, then use --replace.")
        target.parent.mkdir(parents=True, exist_ok=True)
        atomic_write(target, text)


def read_guide(path: Path):
    if is_redirect(path) or not path.is_file():
        raise AdvisorError("Specify a regular public guide file.")
    text = path.read_text(encoding="utf-8-sig")
    return public_guide(text), text


def guide_digest(text: str, repository: str):
    # Bind approval to the destination and the exact text passed to GitHub.
    return hashlib.sha256(f"{repository.lower()}\n{text}".encode("utf-8")).hexdigest()


def submit_guide(metadata: PublicGuide, text: str, repository: str, approval: str | None):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9-]*/[A-Za-z0-9_][A-Za-z0-9_.-]*", repository):
        raise AdvisorError("Use an owner/repository GitHub destination.")
    if approval is None:
        print(f"Preview only. Destination {repository}, guide {metadata.key}.")
        print(f"Review the guide and pass --approve {guide_digest(text, repository)} to publish it.")
        return
    if approval != guide_digest(text, repository):
        raise AdvisorError("The approved digest differs from this guide. Review the current file.")
    with tempfile.TemporaryDirectory(prefix="advisorskill-share-") as directory:
        body = Path(directory) / GUIDE_NAME
        body.write_bytes(text.encode("utf-8"))
        try:
            result = subprocess.run([
                "gh", "issue", "create", "--repo", f"github.com/{repository}", "--title", f"[Guide] {metadata.key}",
                "--body-file", str(body),
            ], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
        except FileNotFoundError:
            raise AdvisorError("GitHub CLI is required to submit a guide.") from None
        except subprocess.TimeoutExpired:
            raise AdvisorError("GitHub did not confirm submission. Check Issues before retrying.") from None
    url = result.stdout.strip()
    try:
        parsed = urlsplit(url)
    except ValueError:
        raise AdvisorError("GitHub did not confirm submission. Check Issues before retrying.") from None
    prefix = f"/{repository}/issues/"
    if (result.returncode or parsed.scheme != "https" or parsed.netloc != "github.com"
            or not parsed.path.lower().startswith(prefix.lower()) or not parsed.path[len(prefix):].isdigit()
            or parsed.query or parsed.fragment):
        raise AdvisorError("GitHub did not confirm submission. Check Issues and gh auth status before retrying.")
    print(url)


def validate_registry(root: Path):
    if not root.is_dir():
        raise AdvisorError("Registry directory does not exist.")
    count = 0
    for path in root.rglob(GUIDE_NAME):
        relative = path.relative_to(root)
        if len(relative.parts) != 3 or any(is_redirect(part) for part in (path, path.parent, path.parent.parent)):
            raise AdvisorError("Registry guides must use regular <discipline>/<advisor>/GUIDE.md paths.")
        metadata, _ = read_guide(path)
        if relative.parts[:2] != (metadata.discipline, metadata.advisor):
            raise AdvisorError("Registry guide metadata does not match its path.")
        count += 1
    print(f"Validated {count} public guide(s).")
