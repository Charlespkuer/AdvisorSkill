import subprocess
from pathlib import Path

from advisorskill.cli import main
from advisorskill.publish import guide_digest, read_guide
from advisorskill.storage import load_state

FIXTURES = Path(__file__).parent / "fixtures"


def test_public_guide_end_to_end(tmp_path, monkeypatch, capsys):
    state = tmp_path / "private"
    output = tmp_path / "draft"
    registry = tmp_path / "registry"

    def command(name, *args):
        return main([name, "--workspace", str(state), *map(str, args)])

    assert command("init", "--id", "private-profile", "--display-name", "PRIVATE_PROFILE") == 0
    assert command("ingest", "--input", FIXTURES / "round-1.jsonl") == 0
    assert command("apply", "--proposal", FIXTURES / "add-rules.yaml", "--approve") == 0
    assert command("export-public", "--discipline", "phy", "--advisor", "alias",
                   "--license", "CC-BY-4.0", "--rule", "R-001", "--output", output) == 0
    guide = output / "phy" / "alias" / "GUIDE.md"
    metadata, text = read_guide(guide)
    assert metadata.key == "phy/alias"
    assert "R-001" in text and "R-002" not in text
    for private in ("PRIVATE_PROFILE", "SYNTHETIC_DRAFT_MARKER", load_state(state).feedback[0].id):
        assert private not in text

    calls = []
    repository = "Example/AdvisorSkill"

    def issue(args, **kwargs):
        calls.append(args)
        assert args[:6] == ["gh", "issue", "create", "--repo", f"github.com/{repository}", "--title"]
        assert Path(args[-1]).read_bytes() == text.encode("utf-8")
        return subprocess.CompletedProcess(args, 0, f"https://github.com/{repository}/issues/42\n", "")

    monkeypatch.setattr(subprocess, "run", issue)
    base = ["submit-guide", "--guide", str(guide), "--repo"]
    approval = guide_digest(text, repository)
    assert main([*base, repository]) == 0
    assert approval in capsys.readouterr().out
    assert main([*base, "Other/AdvisorSkill", "--approve", approval]) == 1
    assert not calls
    assert main([*base, repository, "--approve", approval]) == 0
    assert len(calls) == 1
    assert "/issues/42" in capsys.readouterr().out

    accept = ["accept-guide", "--guide", str(guide), "--registry", str(registry), "--approve"]
    assert main(accept) == 0
    target = registry / "phy" / "alias" / "GUIDE.md"
    assert target.read_bytes() == guide.read_bytes()
    guide.write_text(text + "\nSynthetic update.\n", encoding="utf-8")
    assert main([*base, repository, "--approve", approval]) == 1
    assert len(calls) == 1
    assert main(accept) == 1
    assert target.read_text(encoding="utf-8") == text
    assert main([*accept, "--replace"]) == 0
    assert main(["validate-registry", "--registry", str(registry)]) == 0


def test_guide_traversal_is_rejected_before_writes(tmp_path):
    guide = tmp_path / "guide.md"
    guide.write_text(
        "---\nformat: advisorskill-guide-v1\ndiscipline: ../escape\nadvisor: a\n"
        "license: CC0-1.0\n---\n\nA synthetic rule.\n",
        encoding="utf-8",
    )
    output = tmp_path / "registry"
    assert main(["accept-guide", "--guide", str(guide), "--registry", str(output), "--approve"]) == 1
    assert not output.exists()
