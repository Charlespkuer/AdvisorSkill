# Share an advisor guide within a research group

Use a Git repository whose access is limited to your group, such as an organization-owned private repository or an institution-managed Git service. Members see the evidence accepted into that repository. Set membership according to who may hold a copy of the unpublished material. The institution or repository administrator manages access and review permissions.

AdvisorSkill works against a local checkout. Git handles sign-in, membership, review, and synchronization. Use a dedicated checkout and team workspace for each group.

## Set up or join a group

Clone the approved private repository into an ignored directory such as `.advisorskill/group-checkout`. A maintainer initializes it once and publishes `team.json` to the private repository:

```bash
advisorskill team init --team .advisorskill/group-checkout --id phy-lab --discipline phy
```

Members joining later clone that repository. Keep three locations distinct:

- Your personal workspace, such as `.advisorskill/phy/sxz`.
- The private team checkout, here `.advisorskill/group-checkout`.
- A local team workspace, here `.advisorskill/group-view`, reconstructed from the checkout.

## Student A contributes a round

Ask your agent to show you exactly which comments, excerpts, and source metadata it would share. Confirm that these records are authorized for the group. Use the same manuscript slug as other students working on that manuscript. Supply a different round slug for separate contributions. Repeat `--feedback` to select multiple IDs.

```bash
advisorskill team contribute --team .advisorskill/group-checkout --workspace .advisorskill/phy/sxz --paper paper-a --round r1 --feedback FEEDBACK_ID
```

Use the displayed digest on the same command with `--approve DIGEST`. The command writes `feedback/paper-a/r1.json` in the checkout. Submit that file via a branch and pull request in the private repository. A correction can be shared together with its parent record or after the parent is in the repository.

## A maintainer reviews proposed rules

Start from the updated private checkout. Rebuild the local team workspace and ask the agent to draft a proposal from its task packet. Use the team's remapped evidence IDs and manuscript labels in the packet. This keeps evidence from different manuscripts distinct even if the original comment IDs matched.

```bash
advisorskill team sync --team .advisorskill/group-checkout --workspace .advisorskill/group-view
advisorskill prepare --workspace .advisorskill/group-view
advisorskill review --workspace .advisorskill/group-view --proposal reviewed-proposal.yaml
advisorskill team record --team .advisorskill/group-checkout --proposal reviewed-proposal.yaml --approve
advisorskill team validate --team .advisorskill/group-checkout
```

Keep proposal and summary files in a private workspace. Use `--reject` in `team record` to retain a rejection in the decision history. Submit the new `decisions/NNNNNNNN.json` to the private repository. Serialize these review decisions against the latest checkout. If another decision lands first, sync and review again against the current baseline. Set repository review permissions to enforce who may accept changes.

## Student B uses the guide

Pull the latest accepted changes in the private checkout and run:

```bash
advisorskill team sync --team .advisorskill/group-checkout --workspace .advisorskill/group-view
advisorskill build --workspace .advisorskill/group-view --output .agents/skills
```

Use `.dsh/skills` as the output for DSH. Ask the agent to use `advisor-phy-lab` when reviewing your paper. The built skill contains approved rules. Source evidence stays in the private checkout and local team workspace for authorized review. Fetch and rebuild to pick up future decisions.

The shared files are `team.json`, `feedback/<manuscript>/<round>.json`, and `decisions/NNNNNNNN.json`. Stage these paths explicitly. Local lock files, derived workspaces, private draft proposals, and generated skills stay out of the team history. For public tips, use [public sharing](sharing.md) after approval for that audience.
