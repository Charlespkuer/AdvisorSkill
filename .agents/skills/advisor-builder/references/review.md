# Preparing a review

The task packet contains the profile, evidence, current rules, rule history, decisions, and the baseline revision. Point the reviewer to evidence IDs and summarize the reasoning in your own words.

```yaml
proposal_id: inspect-claim-scope
base_revision: 0
status: pending
rationale: "This comment concerns the introduction of a single draft."
risks:
  - "The rule may require an exception for an abstract."
conflicts: []
operations:
  - type: no_change
    evidence_ids:
      - REPLACE_WITH_AN_ID_FROM_THE_PACKET
```

For `add` and `revise`, replace the example operation with a `rule` mapping containing `id`, `category`, `statement`, `scope`, `evidence_ids`, and `confidence`. The CLI assigns rule revision and status. The scope mapping contains `level` and optional lists of `sections`, `conditions`, and `exceptions`.

- Category values are `narrative`, `argumentation`, `scientific_claims`, `structure`, `language`, `figures`, `notation`, `citations`, `journal_format`, and `research_method`.
- Scope values are `local_issue`, `manuscript`, `venue`, `field`, and `advisor_preference`. Confidence values are `tentative`, `supported`, and `strong`.
- `attach_evidence` and `flag_conflict` require `rule_id` and `evidence_ids`. A conflict flag also requires `reason`. `deprecate` requires `rule_id`.

Each change must reference a rule or evidence. Mark uncertainties, counterexamples, and conflicts explicitly. Run `review` before asking the author for a decision. The author can record a decision using `apply --approve` or `apply --reject`.

## Write the private proposal summary

In `proposal-summary.md`, summarize the proposal ID, baseline, decisions requested, and any unresolved risks or conflicts. Maintain a `## Lexical observations` section alongside the rule overview. Carry forward earlier observations and add new cases even when an operation leaves the rules unchanged. Deduplicate cases only when the anchored use and feedback event match. Preserve distinct edits in a single comment and separate examples when the same word has distinct uses or was independently reviewed.

For each case, record the original form and the replacement, deletion, or clarification when known. Include the relevant passage or section, the evidence ID resolved through `superseded_feedback`, and a short note about the usage. Mark the source of the second form as a verified edit, an explicit advisor recommendation, or an inference. When the advisor flagged a word and gave no replacement, record that. When the word itself is unclear, keep the anchored note and mark the target as unresolved. Keep both options if the evidence supports different choices in different contexts.

For example, an explicit recommendation to replace `utilize` with `use` in a methods sentence can be noted as a local preference for a plain verb. A question about `significant` in a result can flag an ambiguous statistical meaning while leaving the replacement open. State what each case supports before proposing a broader rule. Keep the concrete cases visible when you group them or propose a reusable editing check. Quote only the terms or fragments needed to identify the choice. Store this summary in the private profile.
