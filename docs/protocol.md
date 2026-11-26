# Local protocol, version 0.1

## Import formats

JSONL accepts one UTF-8 JSON object per nonblank line. A minimal object has `comment`. Optional metadata includes `source` (default `manual`), `source_ref`, `revision`, `thread_ref`, `author_role`, `context_before`, `context_after`, `scope`, `section`, and `created_at` (ISO 8601 with an offset). Missing optional fields are stored as null. The importer assigns the `id` and sets visibility to `private`. See [the first demo input](../tests/fixtures/round-1.jsonl).

For passage-specific feedback, `context_before` is the relevant excerpt from the draft the advisor annotated. `context_after` is the excerpt from the actual revised draft, when available. Record the smallest passage that makes the comment intelligible, plus its section and source metadata when known. The builder collects these excerpts from supplied or authorized material before importing. Use null when the passage or revision cannot be verified. See [context capture](../.agents/skills/advisor-builder/references/extraction.md).

For Markdown, start each comment with the exact heading `## Feedback`. Optional sections begin with `### Context before`, `### Context after`, or `### Metadata`. Put plain Markdown text in the comment and context sections, and a YAML mapping in the metadata section. These four headings are reserved as delimiters. See [the second demo input](../tests/fixtures/round-2.md).

Use a stable source record ID in `source_ref` and a new `revision` when editing feedback from the same source. When either value is absent, identity incorporates normalized content. Identity normalizes Unicode to NFC, standardizes newlines, and trims outer whitespace. The workspace retains the original recorded content. Importing identical feedback again is a no-op. A conflicting record for an existing source and revision fails the whole import.

To correct the context of a stored feedback record, import a new row with its ID in `supersedes`, preserving its source, source reference, revision, and comment. The CLI keeps the older record and its audit references. The agent follows `prepare.json`'s `superseded_feedback` links to the latest context during analysis.

## Proposals and persistence

`prepare` atomically refreshes the private `prepare.json` task packet. After new feedback or a decision, run it again before asking the host to draft another proposal.

An agent writes a pending YAML proposal containing a unique proposal ID, the packet's numeric `base_revision`, a rationale, optional risks and conflicts, and one or more ordered operations. Use the generated [proposal schema](../schemas/proposal.schema.json) or [the demo transactions](../tests/fixtures). Reference workspace IDs and paraphrase evidence inside proposals. Keep source comments and relevant manuscript excerpts in the evidence records.

- `add` and `revise` carry a complete rule. Follow the scope and confidence enums in the [rule schema](../schemas/rule.schema.json).
- `attach_evidence` adds new evidence IDs while retaining the current rule statement, confidence, and status.
- `flag_conflict` records conflicting evidence and the reason. Approval suspends the rule from builds until a reviewer approves a resolution.
- `deprecate` retires an existing rule. `no_change` records an observation with a rule or evidence reference.

`review` computes a diff without modifying workspace state. `apply --approve` applies the whole proposal and advances the profile revision once. `apply --reject` records the decision and keeps the current rules and revision. Stale baselines and already-decided proposal IDs fail. The baseline tracks rule decisions, so an evidence-only import leaves it unchanged.

The workspace stores profile metadata, immutable feedback imported through the CLI, current rules, historical rule revisions, and decisions in a single `state.json`. The CLI serializes mutations and atomically replaces the state file. `validate` checks evidence IDs and replays decisions to verify rule provenance. Keep local backups of private data according to your own storage policy.

## Skill artifacts

`build` takes an output parent and creates `advisor-<profile-id>/SKILL.md` with topic references for active rules. It includes rule IDs and reviewed rule text, with raw evidence retained in the workspace. Identical active rules yield identical artifact bytes. A rebuild replaces an existing generated directory only when its checksums still match. Keep manual edits in a separate copy. Adapter integrations, live host validation, and public registry export are later milestones.
