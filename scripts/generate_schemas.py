"""Regenerate JSON Schemas from the Pydantic models."""

import json
from pathlib import Path

from advisorskill.models import Feedback, Profile, Proposal, Rule

ROOT = Path(__file__).resolve().parents[1]

for name, entity in {
    "feedback": Feedback,
    "profile": Profile,
    "proposal": Proposal,
    "rule": Rule,
}.items():
    schema = {"$schema": "https://json-schema.org/draft/2020-12/schema", **entity.model_json_schema()}
    path = ROOT / "schemas" / f"{name}.schema.json"
    path.write_text(
        json.dumps(schema, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(path.relative_to(ROOT))
