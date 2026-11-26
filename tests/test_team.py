import json
import re
import shutil
from pathlib import Path

from advisorskill.cli import main
from advisorskill.storage import load_state

FIXTURES = Path(__file__).parent / "fixtures"


def personal(workspace, action, *args):
    return main([action, "--workspace", str(workspace), *map(str, args)])


def team(root, action, *args):
    return main(["team", action, "--team", str(root), *map(str, args)])


def shared_batch(root, workspace, paper, round_id, *evidence_ids):
    arguments = ["--workspace", workspace, "--paper", paper, "--round", round_id]
    for evidence in evidence_ids:
        arguments.extend(("--feedback", evidence))
    return arguments


def preview(root, arguments, capsys):
    assert team(root, "contribute", *arguments) == 0
    return re.search(r"--approve ([a-f0-9]{64})", capsys.readouterr().out).group(1)


def test_team_contribute_review_and_sync_between_students(tmp_path, capsys):
    first = tmp_path / "student-a"
    peer = tmp_path / "student-b"
    root = tmp_path / "shared-checkout"
    assert personal(first, "init", "--id", "student-a") == 0
    assert personal(peer, "init", "--id", "student-b") == 0
    for workspace in (first, peer):
        assert personal(workspace, "ingest", "--input", FIXTURES / "round-1.jsonl") == 0
    assert team(root, "init", "--id", "phy-team") == 0

    evidence, keep_private = load_state(first).feedback
    arguments = shared_batch(root, first, "paper-a", "r1", evidence.id)
    approval = preview(root, arguments, capsys)
    assert not (root / "feedback").exists()
    assert team(root, "contribute", *arguments, "--approve", "0" * 64) == 1
    assert not (root / "feedback").exists()
    assert team(root, "contribute", *arguments, "--approve", approval) == 0
    assert team(root, "contribute", *arguments, "--approve", approval) == 0
    path = root / "feedback" / "paper-a" / "r1.json"
    assert keep_private.id not in path.read_text(encoding="utf-8")
    conflict = shared_batch(root, first, "paper-a", "r1", keep_private.id)
    assert team(root, "contribute", *conflict) == 1

    # The same local ID in another manuscript must represent separate evidence.
    arguments = shared_batch(root, peer, "paper-b", "r1", evidence.id)
    approval = preview(root, arguments, capsys)
    assert team(root, "contribute", *arguments, "--approve", approval) == 0
    reviewer = tmp_path / "reviewer-cache"
    assert team(root, "sync", "--workspace", reviewer) == 0
    assert personal(reviewer, "prepare") == 0
    packet = json.loads((reviewer / "prepare.json").read_text(encoding="utf-8"))
    assert sorted(packet["team"]["feedback_papers"].values()) == ["paper-a", "paper-b"]
    assert len({item["id"] for item in packet["feedback"]}) == 2

    proposal = tmp_path / "proposal.json"
    payload = {
        "proposal_id": "first-review",
        "base_revision": 0,
        "rationale": "Illustrate a scoped presentation preference.",
        "operations": [{
            "type": "add",
            "rule": {
                "id": "R-001", "category": "narrative",
                "statement": "Explain the motivation before giving the bound.",
                "scope": {"level": "manuscript", "sections": ["introduction"]},
                "evidence_ids": [packet["feedback"][0]["id"]],
            },
        }],
    }
    proposal.write_text(json.dumps(payload), encoding="utf-8")
    assert personal(reviewer, "review", "--proposal", proposal) == 0
    assert personal(reviewer, "apply", "--proposal", proposal, "--approve") == 1
    assert team(root, "record", "--proposal", proposal, "--reject") == 0
    payload["proposal_id"] = "second-review"
    proposal.write_text(json.dumps(payload), encoding="utf-8")
    assert team(root, "record", "--proposal", proposal, "--approve") == 0
    assert team(root, "validate") == 0

    clone = tmp_path / "student-b-checkout"
    shutil.copytree(root, clone, ignore=shutil.ignore_patterns(".advisorskill.lock"))
    cache = tmp_path / "student-b-cache"
    assert team(clone, "sync", "--workspace", peer) == 1
    assert len(load_state(peer).feedback) == 2
    assert team(clone, "sync", "--workspace", cache) == 0
    assert team(clone, "sync", "--workspace", cache) == 0
    assert personal(cache, "validate") == 0
    assert load_state(cache).profile.revision == 1
    assert [decision.status for decision in load_state(cache).decisions] == ["rejected", "accepted"]

    output = tmp_path / "student-b-skills"
    assert personal(cache, "build", "--output", output) == 0
    narrative = output / "advisor-phy-team" / "references" / "narrative.md"
    assert "Explain the motivation before giving the bound." in narrative.read_text(encoding="utf-8")
    for file in output.rglob("*.md"):
        assert "SYNTHETIC_DRAFT_MARKER" not in file.read_text(encoding="utf-8")


def test_team_replays_corrections_across_rounds(tmp_path, capsys):
    workspace = tmp_path / "personal"
    root = tmp_path / "team"
    assert personal(workspace, "init", "--id", "member") == 0
    assert personal(workspace, "ingest", "--input", FIXTURES / "round-1.jsonl") == 0
    assert team(root, "init", "--id", "team") == 0

    before = load_state(workspace).feedback[0]
    data = before.model_dump(mode="json", exclude={"id"})
    data.update(supersedes=before.id, context_before="Corrected synthetic excerpt.")
    input_path = tmp_path / "correction.jsonl"
    input_path.write_text(json.dumps(data), encoding="utf-8")
    assert personal(workspace, "ingest", "--input", input_path) == 0
    corrected = load_state(workspace).feedback[-1]
    arguments = shared_batch(root, workspace, "paper", "a-fix", corrected.id)
    assert team(root, "contribute", *arguments) == 1
    assert not (root / "feedback").exists()
    original = shared_batch(root, workspace, "paper", "z-original", before.id)
    approval = preview(root, original, capsys)
    assert team(root, "contribute", *original, "--approve", approval) == 0
    approval = preview(root, arguments, capsys)
    assert team(root, "contribute", *arguments, "--approve", approval) == 0
    cache = tmp_path / "cache"
    assert team(root, "sync", "--workspace", cache) == 0
    older, latest = load_state(cache).feedback
    assert latest.supersedes == older.id
    assert latest.context_before == "Corrected synthetic excerpt."
    assert older.id != before.id
    assert personal(cache, "validate") == 0
