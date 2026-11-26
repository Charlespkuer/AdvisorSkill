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
