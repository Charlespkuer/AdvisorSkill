# AdvisorSkill

[简体中文](README.md)

Does your paper still sound like AI after all those rounds of edits with your agent?

**AdvisorSkill turns your advisor’s comments into a writing guide your agent can use when revising a paper.** The agent drafts rules from the feedback and the passages it refers to. You decide which rules to keep. On the next draft, the agent can use the guide and explain which rule backs each suggestion.

Does your advisor keep asking you to explain the physical question before the methods? Save that as a rule and give your agent something concrete to check in the next abstract.

The Skill can remember feedback on specific passages, down to individual word choices and suggested phrase replacements.

After you edit the paper yourself, the agent can also flag earlier advice you may have missed.

Raw comments and manuscript excerpts stay local by default. See what a guide looks like in the [public registry](registry/profiles/).

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

## Tips for getting more out of AdvisorSkill

Keep using the same profile over time. Different agents can collect feedback across rounds, helping the guide reflect your advisor’s tastes more closely.

Students with the same advisor can also share a guide and improve their writing together. (That’s the hope, anyway.)

## Share a guide with your labmates

> **When your advisor makes a suggestion once, the whole group can use it next time.**

Students with the same advisor can use a private team repository. Contribute authorized feedback and excerpts by manuscript and round. A maintainer reviews the rules, then labmates sync and use the guide in their own Codex or DSH manuscript projects. Specific word and phrase choices can still be traced to their feedback and context.

Ask your agent to “Share this round of feedback with the lab. Show me which records you selected first.” When revising, try “Sync the team’s advisor guide and use it to check my abstract.” Personal workspaces stay local. Rules authorized for public release follow the public submission workflow. [Private team collaboration](docs/team.md)

## Share a public guide

AdvisorSkill is designed to grow with its community. Anyone can contribute a guide distilled from their own advisor’s feedback. As the collection grows, agents have more guidance to draw on when helping with academic writing.

For example, ask the agent to turn rules `R-001` and `R-003` from `phy/sxz` into a public draft. After you review the text, license, and destination repository, the agent can submit that exact Markdown as a GitHub issue. Maintainers review contributions and keep one accepted guide per advisor at `registry/profiles/<discipline>/<advisor>/GUIDE.md`. To use a private runtime guide in your manuscript project, build directly into its `.agents/skills` (Codex) or `.dsh/skills` (DSH).

[Sharing a public guide](docs/sharing.md) · [Input formats and transaction semantics](docs/protocol.md) · [Windows setup](README.md#在-windows-上运行) · [Contributing](CONTRIBUTING.md)
