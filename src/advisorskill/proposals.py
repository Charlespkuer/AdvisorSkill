"""Preview and apply explicitly reviewed rule transactions."""

from pathlib import Path

from advisorskill.models import (
    Add, AttachEvidence, Deprecate, Feedback, FlagConflict, NoChange, Proposal,
    Revise, Rule, WorkspaceState,
)
from advisorskill.serialization import read_yaml
from advisorskill.storage import AdvisorError, parse_record


def load_proposal(path: Path):
    data = read_yaml(path.read_text(encoding="utf-8-sig"), "Proposal")
    proposal = parse_record(Proposal, data, "Proposal")
    if proposal.status != "pending":
        raise AdvisorError("Proposal files must have pending status.")
    return proposal


def require_evidence(ids, feedback: dict[str, Feedback]):
    if len(set(ids)) != len(ids):
        raise AdvisorError("An evidence list contains duplicate IDs.")
    if not set(ids).issubset(feedback):
        raise AdvisorError("An evidence reference does not exist in this workspace.")


def simulate(state: WorkspaceState, proposal: Proposal):
    if proposal.base_revision != state.profile.revision:
        raise AdvisorError(
            f"Stale proposal baseline. Prepare a new proposal for revision {state.profile.revision}."
        )
    if any(item.proposal_id == proposal.proposal_id for item in state.decisions):
        raise AdvisorError("This proposal ID already has a recorded decision.")

    rules = {rule.id: rule for rule in state.rules}
    feedback = {item.id: item for item in state.feedback}
    history = list(state.history)
    for index, operation in enumerate(proposal.operations, 1):
        try:
            rule_id, updated_rule = apply_operation(operation, rules, feedback)
        except AdvisorError as error:
            raise AdvisorError(f"Operation {index} ({operation.type}). {error}") from None
        if updated_rule is None:
            continue
        if rule_id in rules:
            history.append(rules[rule_id])
        rules[rule_id] = updated_rule

    return state.model_copy(update={
        "rules": tuple(sorted(rules.values(), key=lambda rule: rule.id)),
        "history": tuple(history),
    })


def apply_operation(operation, rules: dict[str, Rule], feedback: dict[str, Feedback]):
    if isinstance(operation, (Add, Revise)):
        require_evidence(operation.rule.evidence_ids, feedback)
        rule_id = operation.rule.id
        previous = rules.get(rule_id)
        if isinstance(operation, Add) and previous is not None:
            raise AdvisorError("The new rule ID already exists.")
        if isinstance(operation, Revise) and previous is None:
            raise AdvisorError("The rule being revised does not exist.")
        rule = Rule(
            **operation.rule.model_dump(),
            status="active",
            revision=1 if previous is None else previous.revision + 1,
        )
        return rule_id, rule

    rule_id = operation.rule_id
    previous = rules.get(rule_id)
    if rule_id is not None and previous is None:
        raise AdvisorError("The referenced rule does not exist.")

    if isinstance(operation, NoChange):
        require_evidence(operation.evidence_ids, feedback)
        if rule_id is None and not operation.evidence_ids:
            raise AdvisorError("A no_change operation needs a rule or evidence reference.")
        return rule_id, None

    if isinstance(operation, Deprecate):
        if previous.status == "deprecated":
            raise AdvisorError("The rule is already deprecated.")
        changes = {"status": "deprecated"}
    else:
        require_evidence(operation.evidence_ids, feedback)
        evidence_ids = tuple(dict.fromkeys((*previous.evidence_ids, *operation.evidence_ids)))
        changes = {"evidence_ids": evidence_ids}
        if isinstance(operation, FlagConflict):
            if previous.status not in {"active", "conflicted"}:
                raise AdvisorError("Only active or conflicted rules can be flagged.")
            changes["status"] = "conflicted"
        elif isinstance(operation, AttachEvidence) and evidence_ids == previous.evidence_ids:
            raise AdvisorError("The rule already links all of the supplied evidence.")
    return rule_id, previous.model_copy(update={**changes, "revision": previous.revision + 1})


def decide(state: WorkspaceState, proposal: Proposal, *, approve: bool):
    proposed_state = simulate(state, proposal)
    decision = proposal.model_copy(update={"status": "accepted" if approve else "rejected"})
    if approve:
        state = proposed_state.model_copy(update={
            "profile": state.profile.model_copy(update={"revision": state.profile.revision + 1}),
        })
    return state.model_copy(update={"decisions": (*state.decisions, decision)})
