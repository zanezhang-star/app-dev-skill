# app-dev

`app-dev` is a risk-routed Codex skill for implementing and verifying repository changes without imposing the same process on every task.

## Delivery modes

| Mode | Use for | Default overhead |
|---|---|---|
| Fast | Clear, local, reversible changes | One agent, focused verification |
| Standard | Cross-file or regression-sensitive changes | Short task context, optional role delegation |
| Controlled | Data, auth, security, infrastructure, external integrations, or destructive risk | Approval, freshness, and risk-driven gates |

The skill announces the selected mode, accepts user-requested mode changes when safe, and explains when observed risk prevents a downgrade. Interrupted work resumes from fresh task evidence instead of rebuilding the workflow.

## Install

- Personal use: place the `app-dev` folder under `$HOME/.agents/skills/`.
- Repository use: place it under `$REPO_ROOT/.agents/skills/`.
- Restart Codex only if an updated skill is not detected automatically.

Invoke it explicitly with `$app-dev`, or let Codex select it for repository changes that match the scope in `SKILL.md`.

## Validate

Run the bundled regression suite with an available Python 3 interpreter:

```text
python tests/test_context_packets.py -v
```
