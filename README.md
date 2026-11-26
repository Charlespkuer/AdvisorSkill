# AdvisorSkill

[简体中文](README.zh-CN.md)

AdvisorSkill turns feedback on academic manuscripts into reviewed, evidence-linked writing preferences. The host agent drafts proposals. The Python CLI records decisions, checks provenance, and builds a portable Agent Skill from approved rules.

## Run locally

Use Python 3.11 or newer. Create and activate a virtual environment before installing.

```bash
python -m pip install -e ".[test]"
advisorskill --help
python -m pytest
python scripts/demo.py
```

The demo uses two rounds of synthetic feedback and saves its local artifacts under `.advisorskill/`. It covers rule creation, new evidence, an unresolved conflict, a rejected proposal, and repeatable builds.

## Use your own profile

The repository makes [advisor-builder](.agents/skills/advisor-builder/SKILL.md) available for implicit invocation in Codex. Open this repository as a Codex workspace and ask, for example, “Save these advisor comments to phy/sxz.” The builder uses an explicitly selected or uniquely matching private profile. For a first import, ask it to create the profile by specifying its discipline and advisor alias.

The private directory convention is `.advisorskill/<discipline>/<advisor>/`. The [public registry](registry/profiles/) uses the same two-level keys. Each profile keeps evidence, rule revisions, and review decisions in `state.json`. The builder captures the relevant original and revised passages when they are available from supplied or authorized sources. The built Skill contains approved rules for later writing tasks.

```bash
advisorskill init --id phy-sxz --discipline phy --workspace .advisorskill/phy/sxz
advisorskill ingest --workspace .advisorskill/phy/sxz --input PATH_TO_PRIVATE_COMMENTS.jsonl
advisorskill prepare --workspace .advisorskill/phy/sxz
```

Ask your agent to follow [advisor-builder](.agents/skills/advisor-builder/SKILL.md), read the workspace's `prepare.json`, and write `.advisorskill/phy/sxz/proposal.yaml`. Review it before recording a decision.

```bash
advisorskill review --workspace .advisorskill/phy/sxz --proposal .advisorskill/phy/sxz/proposal.yaml
advisorskill apply --workspace .advisorskill/phy/sxz --proposal .advisorskill/phy/sxz/proposal.yaml --approve
advisorskill validate --workspace .advisorskill/phy/sxz
advisorskill build --workspace .advisorskill/phy/sxz --output dist/phy
```

Use `--reject` to record a rejection and preserve the current rules. Re-run `prepare` whenever new evidence or approvals change the material an agent needs to review.

Keep source files, proposals, task packets, and outputs in a private location. Prefer a workspace outside a Git repository or under the ignored `.advisorskill/` directory. Treat every built Skill as private until its authored rules have been reviewed for disclosure. The build uses reviewed rule text and leaves raw evidence in the workspace.

Ask the agent to draft a public guide from selected approved rules, then review the exact document before it opens a GitHub issue. Maintainers keep one accepted guide per advisor at `registry/profiles/<discipline>/<advisor>/GUIDE.md`. To use a private runtime guide in your manuscript project, build directly into its `.agents/skills` (Codex) or `.dsh/skills` (DSH).

[Sharing a public guide](docs/sharing.md) · [Input formats and transaction semantics](docs/protocol.md) · [Windows setup](README.zh-CN.md) · [Contributing](CONTRIBUTING.md)
