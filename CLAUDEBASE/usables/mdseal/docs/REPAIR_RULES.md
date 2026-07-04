# Repair Rules

Deterministic repairs only.

Current rules are intentionally small:

- inline math balance
- unicode minus normalization

Repairs are blocked if they would trip a validation gate or touch a protected zone.
Parser comparison can refuse a repair if the candidate makes structural agreement worse.
KaTeX validation can refuse a repair if the candidate makes math less parseable or introduces unsafe commands.

