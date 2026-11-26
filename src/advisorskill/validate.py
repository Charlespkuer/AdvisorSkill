"""Check immutable evidence IDs and replay the recorded approval history."""

from advisorskill.ingest import content_id
from advisorskill.models import WorkspaceState
from advisorskill.proposals import decide
from advisorskill.storage import AdvisorError


def validate_state(state: WorkspaceState):
    seen = set()
    for record in state.feedback:
        if record.id in seen or content_id(record) != record.id:
            raise AdvisorError("Workspace contains a duplicate or invalid feedback ID.")
        seen.add(record.id)

    replayed = WorkspaceState(
        profile=state.profile.model_copy(update={"revision": 0}),
        feedback=state.feedback,
    )
    for decision in state.decisions:
        if decision.status == "pending":
            raise AdvisorError("The decision log contains a pending proposal.")
        replayed = decide(replayed, decision, approve=decision.status == "accepted")

    if (replayed.profile.revision, replayed.rules, replayed.history) != (
        state.profile.revision, state.rules, state.history,
    ):
        raise AdvisorError("Stored rules, history or revision differ from the approval log.")
