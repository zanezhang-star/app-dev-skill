#!/usr/bin/env python3
"""Generate or validate role-scoped JSON context packets for app-dev."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROLES = {"product", "architect", "developer", "quality"}
TASK_ID_PATTERN = re.compile(r"TASK-\d{8}-\d{3}")
TASK_FILES = {
    "request": "request.md",
    "context": "context.md",
    "plan": "plan.md",
    "acceptance": "acceptance.md",
    "test_plan": "test-plan.md",
    "verification_preflight": "verification-preflight.md",
    "development": "development.md",
    "review": "review.md",
    "test_report": "test-report.md",
    "release_summary": "release-summary.md",
}
PREFLIGHT_FILE = TASK_FILES["verification_preflight"]
RUNTIME_RECEIPT_VERSION = 1
PROJECT_RULE_NAMES = ["AGENTS.md", "HERMES.md", "CLAUDE.md", "README.md", "CONTRIBUTING.md"]
DEFAULT_PROHIBITED_ACTIONS = [
    "git_push", "git_merge", "deploy", "production_database", "read_secrets",
]

ROLE_RULES = {
    "product": {
        "task_files": ["request", "context"],
        "may_read": [
            "business rules and current user-visible behavior directly related to the request",
            "small code or test excerpts only when needed to verify existing behavior",
        ],
        "must_not_read": [
            "development.md", "review.md", "test-report.md", "release-summary.md",
            "other task directories", "full repository source dump", "developer/reviewer subjective conclusions",
        ],
        "evidence_policy": "Separate verified facts, recommendations, and unresolved decisions.",
    },
    "architect": {
        "task_files": ["request", "context", "acceptance", "test_plan", "verification_preflight"],
        "may_read": [
            "relevant architecture, interfaces, data models, permissions, deployment, and test configuration",
            "local code excerpts needed to assess migration, security, performance, or compatibility",
        ],
        "must_not_read": [
            "developer subjective self-assessment", "review.md", "release-summary.md",
            "unrelated historical test reports", "unrelated modules", "full repository source dump",
        ],
        "evidence_policy": "Trace each design decision to verified project facts and acceptance criteria.",
    },
    "developer": {
        "task_files": ["request", "plan", "acceptance", "test_plan", "verification_preflight"],
        "may_read": [
            "code, tests, interfaces, data models, callers, and docs directly related to current acceptance criteria",
            "dependency code needed to diagnose an actual build or test failure",
        ],
        "must_not_read": [
            "superseded plans", "closed decisions", "old review.md", "other task directories",
            "unrelated modules", ".env or secrets",
        ],
        "evidence_policy": "Return commands, exit codes, raw outputs, scoped diff, and consumed snapshot fields.",
    },
    "quality": {
        "task_files": ["request", "plan", "acceptance", "test_plan", "verification_preflight", "test_report"],
        "may_read": [
            "actual scoped git diff and changed code",
            "affected callers, regression tests, interfaces, data, permissions, and non-secret logs needed to verify findings",
        ],
        "must_not_read": [
            "developer completion claim, self-rating, risk opinion, or recommended PASS",
            "controller preset conclusion", "other task reviews", "old release summaries",
            "unrelated full repository source", ".env or secrets",
        ],
        "evidence_policy": "Use only objective evidence: original request, approved contract, code, diff, commands, exit codes, and raw outputs.",
    },
}


def run_git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        text=True,
        capture_output=True,
    )
    if result.returncode:
        raise SystemExit(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def canonical_path(path: Path | str) -> str:
    """Return a stable, case-normalized real path, expanding Windows short paths."""
    return os.path.normcase(os.path.realpath(os.fspath(path)))


def resolved_git_path(root: Path, value: str) -> str:
    path = Path(value)
    if not path.is_absolute():
        path = root / path
    return canonical_path(path)


def git_identity(root: Path) -> dict[str, str]:
    """Identify one exact repository worktree, not merely a commit or branch name."""
    requested = canonical_path(root)
    toplevel = canonical_path(run_git(root, "rev-parse", "--show-toplevel"))
    if requested != toplevel:
        raise SystemExit(
            f"project root must equal git toplevel (project_root={requested}, git_toplevel={toplevel})"
        )
    return {
        "project_root": requested,
        "git_toplevel": toplevel,
        "git_common_dir": resolved_git_path(root, run_git(root, "rev-parse", "--git-common-dir")),
        "git_dir": resolved_git_path(root, run_git(root, "rev-parse", "--git-dir")),
    }


def dirty_worktree(root: Path) -> list[str]:
    """Return project changes while excluding app-dev task bookkeeping."""
    lines = [line for line in run_git(root, "status", "--short").splitlines() if line]
    result = []
    for line in lines:
        relative = line[3:].replace("\\", "/")
        if relative.rstrip("/") == ".hermes" or relative.startswith(".hermes/"):
            continue
        result.append(line)
    return result


def worktree_fingerprint(root: Path) -> str:
    """Fingerprint tracked diffs and untracked metadata without reading secret contents."""
    digest = hashlib.sha256()
    diff = subprocess.run(
        ["git", "-C", str(root), "diff", "--binary", "HEAD", "--", ".", ":(exclude).hermes/**"],
        capture_output=True,
    )
    if diff.returncode:
        raise SystemExit(diff.stderr.decode(errors="replace").strip() or "git diff failed")
    digest.update(diff.stdout)
    untracked = run_git(root, "ls-files", "--others", "--exclude-standard").splitlines()
    for relative in sorted(path for path in untracked if path and not path.replace("\\", "/").startswith(".hermes/")):
        path = root / relative
        try:
            stat = path.stat()
        except OSError:
            continue
        digest.update(relative.encode("utf-8", errors="surrogateescape"))
        digest.update(f"\0{stat.st_size}\0{stat.st_mtime_ns}".encode())
    return digest.hexdigest()


def parse_status(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        if ":" not in raw or raw.startswith((" ", "\t")):
            continue
        key, value = raw.split(":", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] == '"':
            value = value[1:-1]
        values[key.strip()] = value
    return values


def require_status_fields(status: dict[str, str]) -> None:
    required = {
        "task_id", "task_type", "task_level", "current_stage", "status",
        "updated_at", "contract_version", "approved_contract_version",
        "verification_preflight", "delivery_reachability", "limited_delivery_accepted_contract_version",
    }
    missing = sorted(required - status.keys())
    if missing:
        raise SystemExit(f"status.yaml missing fields: {', '.join(missing)}")


def preflight_path(task_dir: Path) -> Path:
    return task_dir / PREFLIGHT_FILE


def require_preflight_artifact(task_dir: Path) -> None:
    path = preflight_path(task_dir)
    if not path.is_file() or not path.read_text(encoding="utf-8").strip():
        raise SystemExit(f"verification preflight artifact must exist and be non-empty: {path}")


def string_list(data: dict[str, Any], key: str, *, required: bool = False) -> list[str]:
    value = data.get(key)
    if value is None and not required:
        return []
    if not isinstance(value, list) or (required and not value):
        qualifier = "non-empty " if required else ""
        raise SystemExit(f"context-manifest.json field {key} must be a {qualifier}string array")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise SystemExit(f"context-manifest.json field {key} must contain only non-empty strings")
    return [item.strip() for item in value]


def load_manifest(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid context-manifest.json: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit("context-manifest.json root must be an object")
    normalized = {
        "packet_version": data.get("packet_version", 1),
        "allowed_paths": string_list(data, "allowed_paths", required=True),
        "protected_paths": string_list(data, "protected_paths"),
        "project_rules": string_list(data, "project_rules"),
        "verified_commands": string_list(data, "verified_commands"),
        "prohibited_actions": string_list(data, "prohibited_actions") or list(DEFAULT_PROHIBITED_ACTIONS),
        "notes": data.get("notes", ""),
    }
    if not isinstance(normalized["packet_version"], int):
        raise SystemExit("context-manifest.json packet_version must be an integer")
    if not isinstance(normalized["notes"], str):
        raise SystemExit("context-manifest.json notes must be a string")
    return normalized


def contract_number(value: str) -> int | None:
    if value in {"", "null", "None", "~"}:
        return None
    try:
        return int(value)
    except ValueError as exc:
        raise SystemExit(f"Invalid contract version: {value}") from exc


def role_paths(skill_root: Path, role: str) -> list[Path]:
    role_file = {
        "product": "product-analyst.md",
        "architect": "solution-architect.md",
        "developer": "developer.md",
        "quality": "quality-reviewer.md",
    }[role]
    return [
        skill_root / "references" / "context-routing.md",
        skill_root / "references" / "verification-preflight-and-risk-matrix.md",
        skill_root / "references" / "context-packets" / "common.md",
        skill_root / "references" / "context-packets" / f"{role}.md",
        skill_root / "references" / "roles" / role_file,
    ]


def snapshot(root: Path, status: dict[str, str]) -> dict[str, str | int | None]:
    return {
        **git_identity(root),
        "git_head": run_git(root, "rev-parse", "HEAD"),
        "current_branch": run_git(root, "branch", "--show-current"),
        "worktree_fingerprint": worktree_fingerprint(root),
        "contract_version": contract_number(status["contract_version"]),
        "approved_contract_version": contract_number(status["approved_contract_version"]),
        "status_updated_at": status["updated_at"],
        "current_stage": status["current_stage"],
        "verification_preflight": status.get("verification_preflight"),
        "delivery_reachability": status.get("delivery_reachability"),
        "limited_delivery_accepted_contract_version": contract_number(
            status.get("limited_delivery_accepted_contract_version", "")
        ),
    }


def validate_role_gate(role: str, snap: dict[str, str | int | None], task_dir: Path) -> None:
    if role not in {"developer", "quality"}:
        return
    current = snap["contract_version"]
    approved = snap["approved_contract_version"]
    if not isinstance(current, int) or current <= 0 or approved != current:
        raise SystemExit(
            f"{role} packet requires approved_contract_version == contract_version > 0 "
            f"(got approved={approved}, current={current})"
        )
    if snap.get("verification_preflight") != "complete":
        raise SystemExit(
            f"{role} packet verification preflight must be complete "
            f"(got {snap.get('verification_preflight') or 'missing'})"
        )
    require_preflight_artifact(task_dir)
    reachability = snap.get("delivery_reachability")
    if reachability not in {"reachable_here", "external_required", "not_reachable"}:
        raise SystemExit(
            f"{role} packet has invalid delivery_reachability: {reachability or 'missing'}"
        )
    limited_acceptance = snap.get("limited_delivery_accepted_contract_version")
    if reachability == "not_reachable" and limited_acceptance != current:
        raise SystemExit(
            f"{role} packet requires limited_delivery_accepted_contract_version "
            f"to equal contract_version when delivery_reachability=not_reachable "
            f"(got accepted={limited_acceptance}, current={current})"
        )


def packet_data(
    root: Path,
    task_dir: Path,
    skill_root: Path,
    role: str,
    status: dict[str, str],
    snap: dict[str, str | int | None],
    manifest: dict[str, Any],
) -> dict[str, Any]:
    rules = ROLE_RULES[role]
    task_paths = [task_dir / TASK_FILES[key] for key in rules["task_files"]]
    must_read = [task_dir / "context-manifest.json", *role_paths(skill_root, role), *task_paths]
    must_read.extend(root / name for name in PROJECT_RULE_NAMES if (root / name).is_file())
    return {
        "packet_version": 2,
        "role": role,
        "task_id": status["task_id"],
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "snapshot": snap,
        "common": {
            "project_root": snap["project_root"],
            "task_dir": str(task_dir),
            "task_type": status["task_type"],
            "task_level": status["task_level"],
            "status": status["status"],
            "verification_preflight": snap["verification_preflight"],
            "delivery_reachability": snap["delivery_reachability"],
            "inline_large_documents": False,
            "controller_must_recheck_snapshot_before_accepting_result": True,
        },
        "runtime_identity_check": {
            "required_before_read_or_action": True,
            "identity_mismatch_exit_code": 3,
            "argv": [
                sys.executable,
                str((skill_root / "scripts" / "build_context_packet.py").resolve()),
                "--project-root", str(snap["project_root"]),
                "--task-id", status["task_id"],
                "--role", role,
                "--check",
                "--runtime-root", "<ACTUAL_RUNTIME_ROOT>",
            ],
        },
        "scope": {
            "boundary_kind": "default_read_and_audit_scope_not_os_sandbox",
            "allowed_paths": manifest["allowed_paths"],
            "protected_paths": manifest["protected_paths"],
            "project_rules": manifest["project_rules"],
            "verified_commands": manifest["verified_commands"],
        },
        "dirty_worktree": dirty_worktree(root),
        "must_read": [str(path.resolve()) for path in must_read],
        "may_read": list(rules["may_read"]),
        "may_read_expansion_policy": "Allowed when needed; return the added path and reason for audit.",
        "must_not_read": list(rules["must_not_read"]),
        "evidence_policy": rules["evidence_policy"],
        "prohibited_actions": manifest["prohibited_actions"],
        "required_return_snapshot": [
            "consumed_project_root", "consumed_git_toplevel", "consumed_git_common_dir",
            "consumed_git_dir", "consumed_current_branch", "consumed_git_head",
            "consumed_worktree_fingerprint", "consumed_contract_version",
            "consumed_approved_contract_version", "consumed_status_updated_at",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--task-id", required=True)
    parser.add_argument("--role", choices=sorted(ROLES), required=True)
    parser.add_argument("--check", action="store_true", help="Fail if the existing JSON packet snapshot is stale")
    parser.add_argument(
        "--runtime-root",
        help="With --check, hard-fail unless this Agent runtime directory is the recorded Git worktree",
    )
    args = parser.parse_args()

    if not TASK_ID_PATTERN.fullmatch(args.task_id):
        raise SystemExit(f"Invalid task ID: {args.task_id}")
    if args.runtime_root and not args.check:
        raise SystemExit("--runtime-root requires --check")
    if args.check and not args.runtime_root:
        raise SystemExit("--check requires --runtime-root so runtime worktree identity cannot be skipped")
    if args.runtime_root and canonical_path(Path.cwd()) != canonical_path(Path(args.runtime_root).expanduser()):
        raise SystemExit(
            "--runtime-root must equal the checker process current working directory; "
            "run the identity check from the Agent actual worktree"
        )

    root = Path(args.project_root).expanduser().resolve()
    task_dir = root / ".hermes" / "tasks" / args.task_id
    status_path = task_dir / "status.yaml"
    if not status_path.is_file():
        raise SystemExit(f"Task status does not exist: {status_path}")
    manifest_path = task_dir / "context-manifest.json"
    if not manifest_path.is_file():
        raise SystemExit(f"Context manifest does not exist: {manifest_path}")

    manifest = load_manifest(manifest_path)
    status = parse_status(status_path)
    require_status_fields(status)
    if status["task_id"] != args.task_id:
        raise SystemExit(f"Task ID mismatch: requested {args.task_id}, status has {status['task_id']}")

    current = snapshot(root, status)
    packet_path = task_dir / "context-packets" / f"{args.role}.json"

    if args.check:
        if not packet_path.is_file():
            raise SystemExit(f"Context packet does not exist: {packet_path}")
        try:
            recorded_packet = json.loads(packet_path.read_text(encoding="utf-8"))
            recorded = recorded_packet["snapshot"]
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise SystemExit(f"Invalid context packet JSON: {packet_path}") from exc
        keys = {
            "project_root", "git_toplevel", "git_common_dir", "git_dir",
            "git_head", "current_branch", "worktree_fingerprint", "contract_version",
            "approved_contract_version", "status_updated_at", "current_stage",
            "verification_preflight", "delivery_reachability",
        }
        stale = {
            key: {"recorded": recorded.get(key), "current": current.get(key)}
            for key in keys if recorded.get(key) != current.get(key)
        }
        if stale:
            print(json.dumps({"status": "STALE", "differences": stale}, ensure_ascii=False, indent=2))
            raise SystemExit(2)

        runtime_identity = None
        if args.runtime_root:
            runtime_root = Path(args.runtime_root).expanduser().resolve()
            runtime_identity = {
                **git_identity(runtime_root),
                "git_head": run_git(runtime_root, "rev-parse", "HEAD"),
                "current_branch": run_git(runtime_root, "branch", "--show-current"),
                "worktree_fingerprint": worktree_fingerprint(runtime_root),
            }
            identity_keys = {
                "project_root", "git_toplevel", "git_common_dir", "git_dir",
                "git_head", "current_branch", "worktree_fingerprint",
            }
            mismatch = {
                key: {"recorded": recorded.get(key), "runtime": runtime_identity.get(key)}
                for key in identity_keys if recorded.get(key) != runtime_identity.get(key)
            }
            if mismatch:
                print(json.dumps(
                    {"status": "IDENTITY_MISMATCH", "differences": mismatch},
                    ensure_ascii=False,
                    indent=2,
                ))
                raise SystemExit(3)

        validate_role_gate(args.role, current, task_dir)
        result = {"status": "FRESH", "packet": str(packet_path)}
        if runtime_identity is not None:
            result["runtime_identity"] = runtime_identity
        print(json.dumps(result, ensure_ascii=False))
        return

    validate_role_gate(args.role, current, task_dir)
    packet_path.parent.mkdir(parents=True, exist_ok=True)
    skill_root = Path(__file__).resolve().parent.parent
    packet = packet_data(root, task_dir, skill_root, args.role, status, current, manifest)
    packet_path.write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(packet_path)


if __name__ == "__main__":
    main()
