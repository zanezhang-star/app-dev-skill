# App Dev Mode Matrix

Use this reference when task risk is not obvious.

## Classification Rule

Choose the highest mode triggered by scope, impact, reversibility, or uncertainty.

Do not downgrade a task merely because the requested code change looks small. A one-line permission or metric change can still be Strict.

## Quick Mode

All of the following should be true:

- behavior is already clear
- change is local and reversible
- no public interface or data contract changes
- no core business or security logic
- no migration
- regression surface is small
- one focused verification can establish confidence

### Minimum Artifacts

- compact task card
- focused branch when code changes
- targeted verification evidence
- diff self-review
- commit or ready-to-commit report

### Automatic Escalation

Escalate to Standard when:

- more modules are affected than expected
- an interface or business rule changes
- tests reveal adjacent regressions
- root cause is uncertain
- implementation requires a non-trivial design choice

## Standard Mode

Use when one or more apply:

- normal feature or behavior change
- several related files or components
- API, validation, state, or workflow changes
- moderate regression risk
- dependency or integration work
- refactor changes observable behavior
- a clear design decision is needed

### Minimum Artifacts

- concise implementation plan
- one approval gate
- isolated branch/worktree
- acceptance tests or equivalent evidence
- independent review
- verification report

### Automatic Escalation

Escalate to Strict when:

- core data or metric semantics are affected
- permissions, security, payment, inventory, orders, or fulfillment are touched
- migration or destructive operations appear
- rollback is difficult
- repeated attempts show the design is unreliable
- scope expands across major subsystems

## Strict Mode

Use when one or more apply:

- database schema, migration, or data repair
- authentication, authorization, permission, or sensitive data
- inventory, order, payment, fulfillment, settlement, or reconciliation
- financial or management-reporting metrics
- shared data models or cross-system contracts
- broad architecture or framework changes
- high-volume batch processing
- irreversible or difficult-to-observe side effects
- production incident remediation
- large or uncertain refactor

### Minimum Artifacts

- design and implementation plan
- explicit approval before implementation
- rollback/recovery plan
- isolated branch/worktree
- risk-focused tests and golden samples
- logical-group reviews plus final branch review
- fresh end-to-end verification evidence
- explicit merge decision

## Examples

| Request | Mode | Reason |
|---|---|---|
| Fix button spacing | Quick | Local, reversible visual change |
| Rename a label | Quick | No behavior or contract impact |
| Add a dashboard filter | Standard | User-visible behavior and multi-file state |
| Change API validation | Standard | Contract and regression impact |
| Fix incorrect inventory calculation | Strict | Core business data and reporting risk |
| Add role-based menu permissions | Strict | Authorization boundary |
| Migrate SQLite data to PostgreSQL | Strict | Data migration and rollback risk |
| Refactor one helper without behavior change | Quick or Standard | Depends on coverage and callers |
| Bug remains after two fixes | Standard or Strict | Root-cause uncertainty |
