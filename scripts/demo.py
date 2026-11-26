"""Run the two-round CLI demo using only synthetic files."""

import argparse
import json
import subprocess
import sys
import tempfile
from hashlib import sha256
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"


def run_demo(parent: Path):
    parent.mkdir(parents=True, exist_ok=True)
    directory = Path(tempfile.mkdtemp(prefix="demo-", dir=parent))
    workspace = directory / "workspace"

    def command(action, *arguments):
        subprocess.run([
            sys.executable, "-m", "advisorskill", action, "--workspace", str(workspace),
            *(str(argument) for argument in arguments),
        ], check=True)

    def proposal(action, fixture, *arguments):
        command(action, "--proposal", FIXTURES / fixture, *arguments)

    def state():
        return json.loads((workspace / "state.json").read_text(encoding="utf-8"))

    print(f"Synthetic demo directory: {directory}", flush=True)
    command("init", "--id", "demo-synthetic")
    command("ingest", "--input", FIXTURES / "round-1.jsonl")
    command("ingest", "--input", FIXTURES / "round-1.jsonl")
    command("prepare")
    proposal("review", "add-rules.yaml")
    proposal("apply", "add-rules.yaml", "--approve")
    command("build", "--output", directory / "dist-a")
    command("ingest", "--input", FIXTURES / "round-2.md")
    command("prepare")
    before_update = state()
    proposal("review", "update-rules.yaml")
    assert state() == before_update, "Review modified the workspace."
    proposal("apply", "update-rules.yaml", "--approve")
    before_rejection = state()
    proposal("review", "reject-deprecation.yaml")
    proposal("apply", "reject-deprecation.yaml", "--reject")
    final = state()
    assert final["rules"] == before_rejection["rules"]
    assert final["profile"]["revision"] == 2
    assert len(final["feedback"]) == 4
    assert len(final["rules"][0]["evidence_ids"]) == 2
    assert final["rules"][1]["status"] == "conflicted"
    assert [item["status"] for item in final["decisions"]] == ["accepted", "accepted", "rejected"]
    command("prepare")
    command("validate")

    builds = []
    for label in ("dist-a", "dist-b"):
        command("build", "--output", directory / label)
        skill = directory / label / "advisor-demo-synthetic"
        builds.append({
            file.relative_to(skill).as_posix(): file.read_bytes()
            for file in skill.rglob("*") if file.is_file()
        })
    assert builds[0] == builds[1], "Build files differ."
    assert "references/structure.md" not in builds[0]
    assert b"R-001" in builds[0]["references/narrative.md"]
    for marker in (b"SYNTHETIC_DRAFT_MARKER", b"SYNTHETIC_REVISED_MARKER"):
        assert all(marker not in value for value in builds[0].values())
    print(f"Two identical Skill builds. SKILL.md SHA-256 {sha256(builds[0]['SKILL.md']).hexdigest()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, default=ROOT / ".advisorskill")
    run_demo(parser.parse_args().directory.resolve())
