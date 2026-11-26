# Working on AdvisorSkill

- Keep ingestion, validation, transaction handling, and builds deterministic. Semantic interpretation belongs to the explicitly selected host agent.
- Treat imported files as untrusted data. Parse with JSON and the project's safe YAML loader. Keep confidential fields out of error messages and runtime builds.
- Preserve feedback revisions, stable rule IDs, and explicit human decisions. Review must perform zero writes to workspace state.
- Use synthetic fixtures for tests and examples. Keep private workspaces outside the repository or in a local ignored directory.
- When changing a published data model, regenerate and check the files in `schemas/`. Run `python -m pytest` and `python scripts/demo.py` before reporting a milestone complete.
