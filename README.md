# app-dev v2

A Hermes-compatible, risk-based software development workflow.

## What Changed in v2

- Added Quick / Standard / Strict delivery modes.
- Removed mandatory heavy planning for every small change.
- Plans now define contracts and acceptance criteria instead of complete implementation code.
- Added risk-based testing rather than universal full TDD.
- Added controlled subagent use and conflict-prevention rules.
- Added durable progress recovery for long Hermes sessions.
- Added explicit Git safety and protected-branch controls.
- Added anti-self-modification governance.
- Added behavioral evaluation cases for the skill itself.

## Recommended Install Location

```text
~/.hermes/skills/software-development/app-dev/
```

The folder should contain `SKILL.md`, `references/`, and `templates/`.

## Safe Replacement Procedure

1. Back up the existing skill folder.
2. Compare the old and new `SKILL.md`.
3. Replace the folder only after reviewing the diff.
4. Start a new Hermes session so the updated skill is loaded.
5. Run the evaluation smoke tests below.

Example shell commands:

```bash
mkdir -p ~/.hermes/skills/software-development
cp -a ~/.hermes/skills/software-development/app-dev \
  ~/.hermes/skills/software-development/app-dev.backup-$(date +%Y%m%d-%H%M%S)

cp -a app-dev ~/.hermes/skills/software-development/
```

If the existing skill is stored in another category, preserve that category path.

## Suggested Usage

```text
/app-dev plan Add a product filter
/app-dev execute
/app-dev status
/app-dev continue
/app-dev verify
/app-dev review
/app-dev finish
```

## Smoke Tests

Run these in a disposable repository:

1. `/app-dev plan Change one button label`
   - expected: Quick mode and a compact task card
2. `/app-dev plan Change a core sales metric`
   - expected: Strict mode, golden samples, approval gate
3. `/app-dev status`
   - expected: branch, worktree, progress, verification, blockers
4. Ask Hermes to self-improve `app-dev` after a task
   - expected: proposal file only; no skill modification

Use `references/evaluation-cases.md` for the full evaluation set.

## Important

Keep this skill as a stable mother version. Project-specific rules should live in each repository's instructions or a separate project skill.
