# app-dev v0.3.2

A Hermes-compatible, role-scoped software delivery workflow.

## What changed

- Added public minimum facts plus role-specific context packets.
- Switched machine context manifests and packets to JSON with standard-library parsing.
- Added Git/worktree/contract snapshot freshness gates.
- Added real-runtime validation reopening, state semantics matrices, contract-vs-defect rules, one-time micro-review, and risk-based test deduplication.
- Kept May Read expansion available and clarified that allowed paths are read/audit scope, not an OS sandbox.
- Added persistent regression tests for packet, snapshot, and process-contract behavior.

## Install

Install this folder as `app-dev` under the active Hermes Profile skills directory. For categorized installations, use `~/.hermes/skills/software-development/app-dev/`; preserve the category path already used by your Profile.

After replacement, start a new Hermes session and verify `skill_view(name="app-dev")` reports `version: 0.3.2`.
