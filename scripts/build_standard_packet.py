#!/usr/bin/env python3
"""Build a lightweight role-scoped packet for Standard Lane delegation."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROLES = {"product", "architect", "developer", "quality"}
PROJECT_RULE_NAMES = ("AGENTS.md", "HERMES.md", "CLAUDE.md", "CONTRIBUTING.md")
PROHIBITED_ACTIONS = (
    "git_push", "git_merge", "deploy", "production_database", "read_secrets",
)
ROLE_DEFAULTS: dict[str, dict[str, list[str]]] = {
    "product": {
        "may_read": ["user-visible behavior and small code excerpts needed to verify existing behavior"],
        "must_not_read": ["developer self-assessment", "unrelated source dump", "other task history"],
    },
    "architect": {
        "may_read": ["relevant interfaces, data models, architecture, configuration, and test setup"],
        "must_not_read": ["developer self-assessment", "unrelated modules", "other task history"],
    },
    "developer": {
        "may_read": ["affected code, tests, callers, interfaces, and direct dependencies"],
        "must_not_read": ["superseded decisions", "unrelated modules", ".env or secrets"],
    },
    "quality": {
        "may_read": ["actual scoped diff, changed code, affected callers, tests, and raw outputs"],
        "must_not_read": ["developer completion claim or self-rating", "controller preset conclusion", ".env or secrets"],
    },
}


def run_git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(root), *args], capture_output=True)
    if result.returncode:
        error = result.stderr.decode("utf-8", errors="replace").strip()
        raise SystemExit(error or f"git {' '.join(args)} failed")
    return result.stdout.decode("utf-8", errors="replace").strip()


def canonical_path(path: Path | str) -> str:
    return os.path.normcase(os.path.realpath(os.fspath(path)))


def require_project_root(root: Path) -> str:
    requested = canonical_path(root)
    toplevel = canonical_path(run_git(root, "rev-parse", "--show-toplevel"))
    if requested != toplevel:
        raise SystemExit(f"project root must equal git toplevel: {root}")
    return toplevel


def within(root: Path, path: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def project_path(root: Path, value: str, *, must_exist: bool = False) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = root / path
    path = path.resolve()
    if not within(root, path):
        raise SystemExit(f"path must stay within project root: {value}")
    if must_exist and not path.is_file():
        raise SystemExit(f"required file does not exist: {path}")
    return path


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def unique(items: list[str]) -> list[str]:
    return list(dict.fromkeys(item.strip() for item in items if item.strip()))


def snapshot(root: Path, brief: Path) -> dict[str, str]:
    return {
        "project_root": require_project_root(root),
        "git_head": run_git(root, "rev-parse", "HEAD"),
        "current_branch": run_git(root, "branch", "--show-current"),
        "task_brief": str(brief),
        "task_brief_sha256": file_sha256(brief),
    }


def packet_path(brief: Path, role: str) -> Path:
    return brief.parent / "context-packets" / f"{role}.json"


def load_packet(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"invalid lightweight packet: {path}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("snapshot"), dict):
        raise SystemExit(f"invalid lightweight packet structure: {path}")
    return data


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--task-brief", required=True)
    parser.add_argument("--role", choices=sorted(ROLES), required=True)
    parser.add_argument("--role-goal")
    parser.add_argument("--scope-path", action="append", default=[])
    parser.add_argument("--must-read", action="append", default=[])
    parser.add_argument("--may-read", action="append", default=[])
    parser.add_argument("--must-not-read", action="append", default=[])
    parser.add_argument("--expected-output")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()

    root = Path(args.project_root).expanduser().resolve()
    if not root.is_dir():
        raise SystemExit(f"project root does not exist: {root}")
    brief = project_path(root, args.task_brief, must_exist=True)
    current = snapshot(root, brief)
    output = packet_path(brief, args.role)

    if args.check:
        recorded = load_packet(output)["snapshot"]
        keys = ("project_root", "git_head", "current_branch", "task_brief", "task_brief_sha256")
        stale = {
            key: {"recorded": recorded.get(key), "current": current.get(key)}
            for key in keys if recorded.get(key) != current.get(key)
        }
        if stale:
            print(json.dumps({"status": "STALE", "differences": stale}, ensure_ascii=False, indent=2))
            raise SystemExit(2)
        print(json.dumps({"status": "FRESH", "packet": str(output)}, ensure_ascii=False))
        return

    if not args.role_goal or not args.role_goal.strip():
        raise SystemExit("--role-goal is required when generating a packet")
    if not args.expected_output or not args.expected_output.strip():
        raise SystemExit("--expected-output is required when generating a packet")
    if not args.scope_path:
        raise SystemExit("at least one --scope-path is required")

    scope_paths = [str(project_path(root, item)) for item in args.scope_path]
    must_read = [brief, *(project_path(root, item, must_exist=True) for item in args.must_read)]
    must_read.extend(root / name for name in PROJECT_RULE_NAMES if (root / name).is_file())
    defaults = ROLE_DEFAULTS[args.role]
    packet = {
        "packet_version": 1,
        "lane": "standard",
        "role": args.role,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "role_goal": args.role_goal.strip(),
        "snapshot": current,
        "scope": {
            "boundary_kind": "default_read_and_audit_scope_not_os_sandbox",
            "paths": unique(scope_paths),
        },
        "must_read": unique([str(path.resolve()) for path in must_read]),
        "may_read": unique([*defaults["may_read"], *args.may_read]),
        "may_read_expansion_policy": "Return each added path and reason.",
        "must_not_read": unique([*defaults["must_not_read"], *args.must_not_read]),
        "expected_output": args.expected_output.strip(),
        "prohibited_actions": list(PROHIBITED_ACTIONS),
        "required_return_snapshot": [
            "consumed_project_root", "consumed_current_branch", "consumed_git_head",
            "consumed_task_brief_sha256",
        ],
        "controller_acceptance": "Recheck the lightweight snapshot and actual scoped diff before accepting the result.",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
