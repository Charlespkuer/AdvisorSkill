# Public writing guides

The private workspace is the source of approved rules. A project can build its local writing Skill directly into its host's project skill directory using `advisorskill build --workspace PATH --output .agents/skills` in Codex or `--output .dsh/skills` in DSH. Rebuild there after approved changes. Use a consistent local profile ID, such as `phy-sxz`, for a stable folder name.

## Contribute from an agent

1. Ask the agent to select specific approved rules, a public two-level alias, and a license. Review the exact draft, including statements, scope, and examples. Check that its content can be publicly shared.
2. After you approve the exact draft and GitHub repository, ask the agent to submit it as an Issue. This uses an authenticated GitHub CLI. The contributor can work from the conversation without creating a branch or PR.
3. Repository maintainers review the Issue and incorporate accepted changes into the advisor's public guide.

```powershell
advisorskill export-public --workspace .advisorskill/phy/sxz --discipline phy --advisor sxz --license CC-BY-4.0 --rule R-001
advisorskill submit-guide --guide public-draft/phy/sxz/GUIDE.md
# Review the exact draft and use the digest shown by the preview.
advisorskill submit-guide --guide public-draft/phy/sxz/GUIDE.md --approve SHA256
```

Repeat `--rule` to select additional rules. If a draft already exists, preserve edited wording by generating a fresh draft under a different `--output` directory. The digest covers the repository and the exact UTF-8 text submitted to GitHub. GitHub Issues are public on a public repository, so share only authorized material.

## Curate an accepted guide

Each advisor's single canonical public file is `registry/profiles/<discipline>/<advisor>/GUIDE.md`. Keep contributor attribution and the source Issue in the PR. Check the declared license, authorization, anonymity, and evidence quality before acceptance. Combine related suggestions into the existing guide before replacing it.

```powershell
gh issue view 42 --repo Charlespkuer/AdvisorSkill --json body --jq .body | Set-Content -Encoding utf8 reviewed-guide.md
advisorskill accept-guide --guide reviewed-guide.md --approve
advisorskill validate-registry
```

For an existing advisor, review the complete merged Markdown and pass `--replace` to the acceptance command. Commit the registry file in the maintainer's review branch. A new issue is a submission awaiting review.
