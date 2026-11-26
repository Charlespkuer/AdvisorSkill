"""Versioned entities shared by the CLI and exported JSON Schemas."""

from datetime import datetime
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StringConstraints, field_validator

Text = Annotated[str, StringConstraints(strict=True, min_length=1, pattern=r"\S")]
ProfileID = Annotated[
    str, StringConstraints(strict=True, max_length=56, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
]
Identifier = Annotated[
    str, StringConstraints(strict=True, max_length=80, pattern=r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
]
FeedbackID = Annotated[str, StringConstraints(strict=True, pattern=r"^fb-[a-f0-9]{64}$")]
PositiveInt = Annotated[int, Field(strict=True, ge=1)]
Revision = Annotated[int, Field(strict=True, ge=0)]


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Category(StrEnum):
    NARRATIVE = "narrative"
    ARGUMENTATION = "argumentation"
    SCIENTIFIC_CLAIMS = "scientific_claims"
    STRUCTURE = "structure"
    LANGUAGE = "language"
    FIGURES = "figures"
    NOTATION = "notation"
    CITATIONS = "citations"
    JOURNAL_FORMAT = "journal_format"
    RESEARCH_METHOD = "research_method"


class FeedbackInput(Record):
    source: Identifier = "manual"
    source_ref: Text | None = None
    revision: Text | None = None
    thread_ref: Text | None = None
    author_role: Text | None = None
    comment: Text
    context_before: str | None = None
    context_after: str | None = None
    supersedes: FeedbackID | None = None
    scope: Text | None = None
    section: Text | None = None
    created_at: AwareDatetime | None = None
    visibility: Literal["private"] = "private"

    @field_validator("created_at", mode="before")
    @classmethod
    def parse_timestamp(cls, value):
        if isinstance(value, str):
            return datetime.fromisoformat(value)
        if value is not None and not isinstance(value, datetime):
            raise ValueError("Use a timezone-aware ISO 8601 date and time.")
        return value


class Feedback(FeedbackInput):
    id: FeedbackID


class Scope(Record):
    level: Literal["local_issue", "manuscript", "venue", "field", "advisor_preference"]
    sections: tuple[Text, ...] = ()
    conditions: tuple[Text, ...] = ()
    exceptions: tuple[Text, ...] = ()


class RuleContent(Record):
    id: Identifier
    category: Category
    statement: Text
    scope: Scope
    evidence_ids: Annotated[tuple[FeedbackID, ...], Field(min_length=1)]
    confidence: Literal["tentative", "supported", "strong"] = "tentative"


class Rule(RuleContent):
    status: Literal["proposed", "active", "deprecated", "conflicted"]
    revision: PositiveInt


class Add(Record):
    type: Literal["add"]
    rule: RuleContent


class Revise(Record):
    type: Literal["revise"]
    rule: RuleContent


class AttachEvidence(Record):
    type: Literal["attach_evidence"]
    rule_id: Identifier
    evidence_ids: Annotated[tuple[FeedbackID, ...], Field(min_length=1)]


class Deprecate(Record):
    type: Literal["deprecate"]
    rule_id: Identifier


class FlagConflict(Record):
    type: Literal["flag_conflict"]
    rule_id: Identifier
    evidence_ids: Annotated[tuple[FeedbackID, ...], Field(min_length=1)]
    reason: Text


class NoChange(Record):
    type: Literal["no_change"]
    rule_id: Identifier | None = None
    evidence_ids: tuple[FeedbackID, ...] = ()


Operation = Annotated[
    Add | Revise | AttachEvidence | Deprecate | FlagConflict | NoChange,
    Field(discriminator="type"),
]


class Proposal(Record):
    proposal_id: Identifier
    base_revision: Revision
    operations: Annotated[tuple[Operation, ...], Field(min_length=1)]
    rationale: Text
    risks: tuple[Text, ...] = ()
    conflicts: tuple[Text, ...] = ()
    status: Literal["pending", "accepted", "rejected"] = "pending"


class Profile(Record):
    schema_version: Literal["0.1"] = "0.1"
    profile_id: ProfileID
    display_name: Text
    discipline: Text | None = None
    language: Text | None = None
    version: Text = "0.1.0"
    revision: Revision = 0
    license: Text | None = None
    visibility: Literal["private"] = "private"
    rules_path: Literal["state.json#/rules"] = "state.json#/rules"
    authorization: Text | None = None


class TeamView(Record):
    directory: Text
    feedback_papers: dict[FeedbackID, ProfileID]


class WorkspaceState(Record):
    profile: Profile
    feedback: tuple[Feedback, ...] = ()
    rules: tuple[Rule, ...] = ()
    history: tuple[Rule, ...] = ()
    decisions: tuple[Proposal, ...] = ()
    team: TeamView | None = None
