"""Replay feedback and decisions from a private team repository checkout."""

import hashlib
import json
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field

from advisorskill.ingest import check_correction, content_id, equivalent
from advisorskill.models import Feedback, Profile, ProfileID, Proposal, Record, TeamView, WorkspaceState
from advisorskill.proposals import decide, load_proposal
from advisorskill.storage import (
    AdvisorError, atomic_write, is_redirect, json_text, load_state, parse_record, resolve_path,
    save_state, unique_object, writer_lock,
)

TEAM_FILE = "team.json"


class TeamManifest(Record):
    format: Literal["advisorskill-team-v1"]
    profile: Profile


class TeamBatch(Record):
    profile_id: ProfileID
    paper: ProfileID
    round: ProfileID
    feedback: Annotated[tuple[Feedback, ...], Field(min_length=1)]


def read_record(path: Path, model, label: str):
    if is_redirect(path) or not path.is_file():
        raise AdvisorError(f"{label} must be a regular file.")
    try:
        data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
    except (UnicodeError, ValueError, RecursionError):
        raise AdvisorError(f"{label} is invalid JSON.") from None
    return parse_record(model, data, label)


def team_profile(root: Path):
    manifest = read_record(root / TEAM_FILE, TeamManifest, "Team manifest")
    if manifest.profile.revision != 0:
        raise AdvisorError("The team manifest must start at revision zero.")
    return manifest.profile


def entries(path: Path):
    if is_redirect(path):
        raise AdvisorError("Team paths must not redirect.")
    if not path.exists():
        return []
    if not path.is_dir():
        raise AdvisorError("Team history must be stored in directories.")
    return sorted(path.iterdir())


def read_batches(root: Path):
    for directory in entries(root / "feedback"):
        for file in entries(directory):
            batch = read_record(file, TeamBatch, "Team evidence batch")
            if (directory.name, file.name) != (batch.paper, f"{batch.round}.json"):
                raise AdvisorError("Team feedback must use feedback/<paper>/<round>.json.")
            yield batch


def combine_feedback(profile: Profile, batches):
    originals = {}
    for batch in batches:
        if batch.profile_id != profile.profile_id:
            raise AdvisorError("Team evidence batch belongs to a different profile.")
        if len({record.id for record in batch.feedback}) != len(batch.feedback):
            raise AdvisorError("Team evidence batch contains duplicate IDs.")
        for record in batch.feedback:
            key = (batch.paper, record.id)
            if content_id(record) != record.id:
                raise AdvisorError("Team evidence has an invalid original ID.")
            previous = originals.setdefault(key, record)
            if not equivalent(previous, record):
                raise AdvisorError("Two team batches disagree on the same evidence ID for a paper.")

    mapped = {}
    feedback = {}
    papers = {}
    superseded = set()
    pending = originals
    # A correction can appear in a batch whose name sorts before its parent batch.
    while pending:
        deferred = {}
        for key, original in pending.items():
            paper, _ = key
            target = (paper, original.supersedes)
            if original.supersedes is not None and target not in mapped:
                deferred[key] = original
                continue
            namespace = hashlib.sha256(
                json_text([profile.profile_id, paper, original.source]).encode("utf-8")
            ).hexdigest()
            transformed = original.model_copy(update={
                "source": f"team-{namespace}", "supersedes": mapped.get(target),
            })
            record = transformed.model_copy(update={"id": content_id(transformed)})
            check_correction(record, feedback, superseded)
            mapped[key] = record.id
            feedback[record.id] = record
            papers[record.id] = paper
        if len(deferred) == len(pending):
            raise AdvisorError("A team context correction needs its parent in the same paper.")
        pending = deferred
    return tuple(feedback.values()), papers


def replay_team(root: Path, extra_batch: TeamBatch | None = None):
    profile = team_profile(root)
    batches = list(read_batches(root))
    if extra_batch is not None:
        batches.append(extra_batch)
    feedback, papers = combine_feedback(profile, batches)
    state = WorkspaceState(
        profile=profile, feedback=feedback,
        team=TeamView(directory=str(root), feedback_papers=papers),
    )
    for index, file in enumerate(entries(root / "decisions"), 1):
        if file.name != f"{index:08d}.json":
            raise AdvisorError("Team decision history must use consecutive numbered JSON files.")
        decision = read_record(file, Proposal, "Team decision")
        if decision.status == "pending":
            raise AdvisorError("Team decision history contains a pending proposal.")
        state = decide(state, decision, approve=decision.status == "accepted")
    return state


def init_team(root: Path, args):
    profile = parse_record(Profile, {
        "profile_id": args.id, "display_name": args.display_name or args.id,
        "discipline": args.discipline,
    }, "Team profile")
    root.mkdir(parents=True, exist_ok=True)
    with writer_lock(root):
        path = root / TEAM_FILE
        if is_redirect(path) or path.exists():
            raise AdvisorError("A team manifest already exists.")
        personal_state = root / "state.json"
        if (is_redirect(personal_state) or personal_state.exists()
                or entries(root / "feedback") or entries(root / "decisions")):
            raise AdvisorError("Choose a new team directory or an empty checkout.")
        atomic_write(path, json_text(TeamManifest(format="advisorskill-team-v1", profile=profile)))
    print("Initialized team ledger. Configure access in your private repository.")


def draft_batch(root: Path, workspace: Path, args):
    if not workspace.is_dir():
        raise AdvisorError("Personal workspace directory does not exist.")
    with writer_lock(workspace):
        personal = load_state(workspace)
    if personal.team is not None:
        raise AdvisorError("Select evidence from a personal workspace.")
    records = {record.id: record for record in personal.feedback}
    selected = set(args.feedback)
    if not selected.issubset(records):
        raise AdvisorError("Each selected feedback ID must exist in the personal workspace.")
    return parse_record(TeamBatch, {
        "profile_id": team_profile(root).profile_id, "paper": args.paper, "round": args.round,
        "feedback": tuple(record for record in personal.feedback if record.id in selected),
    }, "Team evidence batch")


def contribute(root: Path, batch: TeamBatch, approval: str | None):
    folder = root / "feedback" / batch.paper
    path = folder / f"{batch.round}.json"
    for item in (folder.parent, folder, path):
        if is_redirect(item):
            raise AdvisorError("Team contribution paths must not redirect.")
    text = json_text(batch)
    # Bind approval to the exact payload and the selected local team checkout.
    digest = hashlib.sha256(json_text([str(root), text]).encode("utf-8")).hexdigest()
    exists = path.exists()
    if exists:
        prior = read_record(path, TeamBatch, "Existing team evidence batch")
        if prior != batch:
            raise AdvisorError("This paper and round already have different evidence. Use a new round.")
    replay_team(root, extra_batch=None if exists else batch)
    if approval is None:
        print(f"Preview for {batch.profile_id}, {len(batch.feedback)} selected feedback record(s).")
        print(f"Review the exact records and destination, then pass --approve {digest}.")
        return
    if approval != digest:
        raise AdvisorError("Approved digest differs from the selected evidence or team checkout.")
    if not exists:
        folder.mkdir(parents=True, exist_ok=True)
        atomic_write(path, text)
    print(f"Team batch ready at feedback/{batch.paper}/{batch.round}.json.")


def sync_team(workspace: Path, current: WorkspaceState):
    workspace.mkdir(parents=True, exist_ok=True)
    with writer_lock(workspace):
        path = workspace / "state.json"
        if path.exists() or is_redirect(path):
            previous = load_state(workspace)
            if previous.team is None or Path(previous.team.directory) != Path(current.team.directory):
                raise AdvisorError("Choose a dedicated workspace for this team checkout.")
            if (previous.profile.profile_id != current.profile.profile_id
                    or previous.decisions != current.decisions[:len(previous.decisions)]):
                raise AdvisorError("The team checkout would replace existing review history. Check its revision.")
            if previous == current:
                print(f"Team workspace is current at revision {current.profile.revision}.")
                return
        save_state(workspace, current)
    print(f"Synced team revision {current.profile.revision} with {len(current.feedback)} evidence record(s).")


def run_team(args):
    root = resolve_path(args.team)
    if args.team_command == "init":
        init_team(root, args)
        return
    if not root.is_dir():
        raise AdvisorError("Team checkout directory does not exist.")
    workspace = resolve_path(args.workspace) if args.team_command in {"contribute", "sync"} else None
    if workspace is not None and (root == workspace or root in workspace.parents or workspace in root.parents):
        raise AdvisorError("Keep the team checkout and local workspace in separate directories.")
    if args.team_command == "contribute":
        batch = draft_batch(root, workspace, args)
        with writer_lock(root):
            contribute(root, batch, args.approve)
        return
    with writer_lock(root):
        current = replay_team(root)
        if args.team_command == "record":
            reviewed = decide(current, load_proposal(args.proposal), approve=args.approve)
            directory = root / "decisions"
            directory.mkdir(exist_ok=True)
            decision = reviewed.decisions[-1]
            atomic_write(directory / f"{len(reviewed.decisions):08d}.json", json_text(decision))
            print(f"Recorded team decision {decision.status}. Revision {reviewed.profile.revision}.")
        elif args.team_command == "validate":
            print(f"Valid team ledger at revision {current.profile.revision}.")
        else:
            sync_team(workspace, current)
