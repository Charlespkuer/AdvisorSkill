"""Private workspace I/O and cross-process writer locking."""

import json
import os
import stat
import tempfile
from contextlib import contextmanager
from pathlib import Path

from pydantic import BaseModel, ValidationError

from advisorskill.models import WorkspaceState


class AdvisorError(ValueError):
    """An error whose message is safe to show on the CLI."""


def json_text(data):
    if isinstance(data, BaseModel):
        data = data.model_dump(mode="json")
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise AdvisorError("Duplicate mapping key.")
        result[key] = value
    return result


def parse_record(model, data, label):
    try:
        return model.model_validate(data)
    except ValidationError as error:
        problems = set()
        for item in error.errors(include_input=False):
            field = next(iter(item["loc"]), None)
            kind = item["type"]
            problems.add(f"{field}: {kind}" if field in model.model_fields else kind)
        details = ", ".join(sorted(problems))
        raise AdvisorError(f"{label} does not match its schema ({details}).") from None


def resolve_path(path: Path):
    try:
        return path.resolve()
    except RuntimeError:
        raise AdvisorError("The path cannot be resolved.") from None


def is_redirect(path: Path):
    try:
        attributes = path.lstat()
    except FileNotFoundError:
        return False
    return stat.S_ISLNK(attributes.st_mode) or (
        os.name == "nt" and attributes.st_reparse_tag == stat.IO_REPARSE_TAG_MOUNT_POINT
    )


@contextmanager
def writer_lock(directory: Path, name: str = ".advisorskill.lock"):
    # Keep the lock file in place so every process locks the same file.
    path = directory / name
    if is_redirect(path):
        raise AdvisorError("The lock path must be a regular file.")
    with path.open("ab") as lock:
        if os.name == "nt":
            import msvcrt

            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl

            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        yield
        # Closing the handle releases the OS lock, including on exceptions.


def atomic_write(path: Path, text: str):
    descriptor, temp_name = tempfile.mkstemp(prefix=".advisorskill-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as temporary:
            temporary.write(text)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temp_name, path)
    finally:
        Path(temp_name).unlink(missing_ok=True)


def load_state(directory: Path):
    path = directory / "state.json"
    if not path.is_file() or is_redirect(path):
        raise AdvisorError("Workspace has no regular state.json. Run init first.")
    try:
        data = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
    except (UnicodeError, ValueError, RecursionError):
        raise AdvisorError("Workspace state is invalid JSON.") from None
    return parse_record(WorkspaceState, data, "Workspace state")


def save_state(directory: Path, state: WorkspaceState):
    atomic_write(directory / "state.json", json_text(state))
