# Updating rules

- Use `add` for a supported new rule.
- Use `attach_evidence` when additional feedback supports an existing rule. Keep the prior confidence unless the strength, independence, and applicability of the evidence justify an explicit `revise`.
- Use `revise` to change the statement, scope, exceptions, confidence, or evidence list while preserving the rule ID. Explain any evidence removed from a proposed rule.
- Use `deprecate` when the reviewer agrees that a rule should stop applying.
- For conflicting feedback, compare scope, venue, evidence quality, and chronology. Propose a scoped revision if justified. Otherwise use `flag_conflict`, link the evidence, and explain what the reviewer should resolve. Approving the flag suspends the rule until the reviewer approves a resolution.
- Use `no_change` when the evidence calls for no rule update. Link the affected rule or feedback. Re-prepare and reassess if the baseline has moved.
