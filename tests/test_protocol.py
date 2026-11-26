import json
import re
from pathlib import Path

import yaml

from advisorskill.models import Feedback, Profile, Proposal, Rule

ROOT = Path(__file__).resolve().parents[1]


def test_generated_protocol_schemas_match_models():
    for name, entity in {"feedback": Feedback, "profile": Profile, "proposal": Proposal, "rule": Rule}.items():
        file = ROOT / "schemas" / f"{name}.schema.json"
        exported = json.loads(file.read_text(encoding="utf-8"))
        assert exported.pop("$schema") == "https://json-schema.org/draft/2020-12/schema"
        assert exported == entity.model_json_schema()
    profile = ROOT / "templates" / "profile" / "profile.json"
    assert Profile.model_validate_json(profile.read_bytes()).visibility == "private"


def test_builder_skill_metadata_and_references():
    path = ROOT / ".agents" / "skills" / "advisor-builder" / "SKILL.md"
    content = path.read_text(encoding="utf-8")
    _, frontmatter, body = content.split("---\n", 2)
    metadata = yaml.safe_load(frontmatter)
    assert metadata["name"] == path.parent.name
    host_policy = path.parent / "agents" / "openai.yaml"
    assert yaml.safe_load(host_policy.read_text(encoding="utf-8"))["policy"]["allow_implicit_invocation"]
    assert metadata["description"] and len(content.splitlines()) < 500
    links = re.findall(r"\]\((references/[^)]+)\)", body)
    assert len(links) == 3
    assert all((path.parent / target).is_file() for target in links)
