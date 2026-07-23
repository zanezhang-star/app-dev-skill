---
name: app-dev
description: Control application changes with risk-based delivery gates.
version: 2.0.0
author: Zane
metadata:
  hermes:
    tags: [software-development, planning, testing, git, code-review]
    category: software-development
    related_skills: [systematic-debugging, requesting-code-review, test-driven-development]
    requires_toolsets: [terminal]
---

# App Dev

## Purpose

Use this skill for application feature development, bug fixing, refactoring, integration, review, and release preparation.

The goal is not to maximize process. The goal is to use the **lightest process that can safely produce evidence-backed results**.

## Non-Negotiable Rules

1. Inspect the repository, current branch, working tree, project instructions, and relevant tests before editing.
2. Classify the task as **Quick**, **Standard**, or **Strict** before implementation.
3. Do not perform routine development directly on `main` or `master`.
4. Do not claim completion without fresh verification evidence.
5. Do not silently expand scope. Reclassify the task when new risk or scope appears.
6. Do not overwrite uncommitted user work.
7. Do not modify this skill or its support files during normal project work.
8. Prefer simple, focused changes. Do not add unrelated refactors or speculative features.
9. Translate technical progress, risk, and results into clear language for the user.
10. User instructions override this skill, except destructive actions still require explicit approval.

## Command Interpretation

When invoked with these intents:

- `/app-dev plan` — inspect and produce a task card or implementation plan. Do not edit production code.
- `/app-dev execute` — implement the approved or current plan.
- `/app-dev continue` — recover state from Git and task records, then resume at the first incomplete step.
- `/app-dev status` — report current branch, worktree state, completed work, verification, blockers, and next action.
- `/app-dev verify` — run the appropriate quality gates and produce a verification report.
- `/app-dev review` — perform an independent scope and code-quality review.
- `/app-dev finish` — verify, summarize, prepare commit/PR/MR or merge options, and wait for approval before changing the protected branch.

If the user gives a development request without a subcommand, classify it and apply the corresponding workflow.

## Step 1: Recover and Inspect Context

Use `terminal`, `read_file`, and `search_files` to determine:

- repository root and project instructions
- current branch and `git status`
- recent relevant commits
- existing architecture and conventions
- changed or related files
- available tests, lint, type-check, build, and CI configuration
- whether a prior task record exists under `.app-dev/`

If the working tree is dirty:

- identify which changes belong to the current task
- preserve unrelated changes
- do not reset, clean, stash, or overwrite them without approval
- prefer a new worktree or a separate branch when isolation is needed

For a resumed task, trust Git history and written task records over uncertain conversational memory.

## Step 2: Choose the Delivery Mode

Load `references/mode-matrix.md` when the classification is not obvious.

### Quick Mode

Use when the change is small, local, reversible, and low-risk.

Typical examples:

- copy, style, layout, or configuration correction
- a clear single-file or tightly scoped change
- a low-risk bug with a known cause
- documentation or non-behavioral cleanup

Required flow:

1. Write a compact task card.
2. Create or confirm a feature/fix branch.
3. Make the smallest correct change.
4. Run targeted verification plus any cheap relevant baseline check.
5. Self-review the diff.
6. Commit or report the ready-to-commit state.

Do not create a long design document, dispatch subagents, or force full TDD unless the actual risk requires escalation.

### Standard Mode

Use for normal features and behavior changes with moderate scope or regression risk.

Typical examples:

- new user-facing function
- API or business-rule change
- multi-file change with clear boundaries
- integration with an existing module
- refactor that changes behavior or interfaces

Required flow:

1. Inspect the codebase.
2. Produce one concise implementation plan covering scope, files, interfaces, acceptance criteria, tests, and risks.
3. Obtain one user approval before coding unless the user already explicitly approved execution.
4. Create an isolated branch or worktree.
5. Implement in independently testable units.
6. Run relevant automated checks.
7. Perform one independent review when `delegate_task` is available; otherwise perform a fresh-context self-review.
8. Fix Important or Critical findings and re-verify.
9. Present completion evidence and Git state.

Do not write complete production code inside the plan. The plan defines contracts and evidence, not every keystroke.

### Strict Mode

Use when failure could corrupt data, expose access, break core reporting, affect revenue operations, or create difficult rollback.

Strict triggers include:

- database schema or migration
- authentication, authorization, roles, or permissions
- inventory, order, payment, fulfillment, reconciliation, or financial logic
- core metric definitions or reporting口径
- destructive operations or irreversible data changes
- broad architecture changes
- large cross-module changes
- security-sensitive work
- repeated failed implementation that indicates the original plan is unreliable

Required flow:

1. Create a design and implementation plan with scope boundaries, interfaces, data flow, failure handling, migration/rollback, acceptance criteria, and test strategy.
2. Obtain explicit approval before production-code changes.
3. Create an isolated branch or worktree and a checkpoint commit where appropriate.
4. Use test-first development for deterministic core rules and bug reproductions where feasible.
5. Split work by meaningful, independently reviewable units—not 2-minute microsteps.
6. Use fresh subagents only for independent workstreams.
7. Review each logical group and perform a final whole-branch review.
8. Run unit, integration, migration, permission, regression, and build checks as applicable.
9. Verify rollback or recovery procedures.
10. Do not merge or push to a protected branch without explicit approval.

## Step 3: Create the Minimum Useful Plan

Use:

- `templates/task-card.md` for Quick mode
- `templates/standard-plan.md` for Standard mode
- the Standard template plus architecture, migration, rollback, and failure-mode sections for Strict mode

A good plan specifies:

- goal and user-visible outcome
- in-scope and out-of-scope items
- files or components expected to change
- interfaces and data contracts
- acceptance criteria
- test and verification evidence
- risks and rollback
- execution order where dependencies exist

A plan must not:

- contain speculative features
- duplicate complete implementation code
- prescribe irrelevant ceremony
- hide uncertain assumptions
- silently include unrelated cleanup

Ask at most one blocking question at a time. When ambiguity is minor, state a reasonable assumption and continue.

## Step 4: Git Safety and Isolation

Before editing:

1. Run `git status --short --branch`.
2. Confirm the current branch is not a protected branch.
3. Create a focused branch when needed:
   - `feature/<short-name>`
   - `fix/<short-name>`
   - `refactor/<short-name>`
   - `chore/<short-name>`
4. Prefer a worktree when parallel agents, long-running work, or a dirty primary checkout creates conflict risk.
5. Commit after an independently testable unit, not after every trivial edit.

This workflow is platform-neutral and works with GitHub or Gitee. Use PR or MR terminology according to the hosting platform.

Never run these without explicit user approval:

- `git reset --hard`
- `git clean -fd` or stronger variants
- `git push --force` or `--force-with-lease`
- deleting branches
- rewriting protected-branch history
- overwriting uncommitted changes
- destructive database operations
- merging or pushing directly to `main`/`master`

For undoing shared history, prefer `git revert`. Use `git reset` only for unshared local history and only with approval.

## Step 5: Implementation Discipline

During implementation:

- follow existing project patterns unless they are directly causing the problem
- keep files focused and interfaces explicit
- change only what serves the accepted goal
- update tests and documentation that are genuinely affected
- record material decisions in the task plan or project documentation
- stop and reclassify if the change touches a Strict trigger
- do not mask errors with broad exception handling, disabled checks, or fake fallback data

When implementation reveals a better approach:

- preserve the accepted outcome and constraints
- update the plan before materially changing architecture or scope
- obtain approval again only when cost, risk, behavior, or scope materially changes

## Step 6: Debugging Protocol

For bugs:

1. Reproduce the failure.
2. Gather evidence and narrow the failing boundary.
3. Identify the root cause.
4. Add a regression test or reliable reproduction where feasible.
5. Apply the smallest root-cause fix.
6. Re-run the reproduction and relevant regression checks.
7. Inspect adjacent behavior for side effects.

Do not apply a sequence of guesses.

If the same issue survives two materially different fix attempts:

- stop patching
- reassess assumptions, architecture, test validity, and environment
- reclassify to Standard or Strict as needed

If a third cycle still produces no reliable progress:

- report the blocker, evidence, rollback state, and recommended next decision
- do not continue consuming time through blind retries

## Step 7: Risk-Based Testing

Testing depth follows risk, not habit.

### Quick

- targeted test or manual verification for the changed behavior
- relevant lint/type/build check when cheap
- inspect the final diff

### Standard

- tests for acceptance criteria and changed business behavior
- regression checks for nearby functionality
- lint/type/build as used by the project
- independent review of scope compliance and code quality

### Strict

- test-first for core deterministic rules and reproducible bugs where feasible
- unit and integration tests
- data migration dry run and validation
- permission/role matrix tests
- golden samples for metrics, reports, or transformation rules
- rollback or recovery verification
- final whole-branch review

Rules:

- do not write tests that merely assert mocks or implementation details when real behavior can be tested
- do not change a failing test only to make it pass unless the requirement changed
- do not claim a command passed unless it was run after the final relevant change
- for UI work, combine automated checks with screenshots or a concrete manual checklist when visual correctness cannot be fully automated

## Step 8: Delegation and Review

Use `delegate_task` only when it reduces risk or context pollution.

### Quick

Do not delegate.

### Standard

Prefer:

- main agent implements
- one fresh reviewer checks accepted scope, diff, and test evidence

### Strict

Use:

- controller agent retains the full plan and decisions
- fresh implementer subagent per independent workstream
- reviewer receives the task brief, diff, and test evidence
- final reviewer checks the complete branch

Delegation rules:

- do not run multiple agents in parallel on overlapping files or dependent tasks
- pass only the task-specific brief and required interfaces, not the full conversation history
- require implementers to report changed files, commits, tests, results, and concerns
- Critical and Important findings block completion
- after fixes, re-run covering tests and re-review
- the controller is responsible for cross-task consistency

If delegation is unavailable, execute inline and explicitly preserve the same review gates.

## Step 9: Durable Progress for Long Tasks

For Standard or Strict work that may span sessions, maintain:

```text
.app-dev/
  current-task.md
  progress.md
  verification.md
  improvement-proposals.md
```

Use existing project conventions when they already provide equivalent files.

Record:

- accepted goal and mode
- branch/worktree
- completed units and commit hashes
- open blockers
- decisions that affect later work
- latest verification commands and results

Do not use the task ledger as a substitute for Git commits.

## Step 10: Completion Contract

Before saying the task is complete:

1. Re-read the accepted goal and acceptance criteria.
2. Inspect the complete diff.
3. Run fresh relevant checks after the final change.
4. Confirm no unrelated changes were introduced.
5. Confirm the branch and working-tree state.
6. Produce the report using `templates/verification-report.md`.

The final report must state:

- what changed
- what did not change
- files or components affected
- verification commands and actual results
- review findings and resolutions
- remaining risks or manual checks
- branch and commit state
- recommended merge/PR/MR or rollback action

Evidence beats confidence. “It should work” is not completion.

## Skill Governance

This file is a stable development-policy master.

During ordinary project work:

- never call `skill_manage` to update, delete, or rewrite `app-dev`
- never patch `SKILL.md`, references, templates, or version metadata
- never accept an automatic “self-improvement” edit to this skill
- write improvement ideas only to `.app-dev/improvement-proposals.md`

An `app-dev` change requires:

1. an explicit user request to upgrade the skill
2. a visible diff
3. a version bump
4. evaluation against `references/evaluation-cases.md`
5. user approval before replacing the active copy

Project-specific rules belong in project instructions or a project-specific skill, not in this general skill.

## References

Load on demand:

- `skill_view("app-dev", "references/mode-matrix.md")`
- `skill_view("app-dev", "references/evaluation-cases.md")`
- `skill_view("app-dev", "templates/task-card.md")`
- `skill_view("app-dev", "templates/standard-plan.md")`
- `skill_view("app-dev", "templates/verification-report.md")`
- `skill_view("app-dev", "templates/improvement-proposal.md")`
