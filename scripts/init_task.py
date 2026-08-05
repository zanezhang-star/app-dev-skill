#!/usr/bin/env python3
"""Create the persistent artifact directory for an app-dev task."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

TYPES = {
    "feature", "fix", "refactor", "performance", "security", "test",
    "documentation", "configuration", "investigation",
}
LEVELS = {"small", "medium", "large"}
FILES = [
    "request.md", "context.md", "plan.md", "acceptance.md",
    "development.md", "review.md", "test-report.md", "release-summary.md",
]

TEST_PLAN_TEMPLATE = """# test-plan.md

## 合同驱动风险测试矩阵

按当前合同和实际风险选择适用维度；不适用项说明原因，不为填表制造测试。

| AC | 主路径 | 边界/规模 | 跨入口一致性 | 权限/错误/状态 | 所需证据 |
|---|---|---|---|---|---|
| 待填写 | 待填写 | 待填写 | 待填写 | 待填写 | 待填写 |

## 验证分层

- 必须执行：待填写
- 建议执行：待填写
- 当前环境无法执行：待填写
"""

PREFLIGHT_TEMPLATE = """# verification-preflight.md

在固定合同和授权开发前完成。只记录已验证能力、未知项和阻断，不读取或写入凭据。

| Gate | 必需验证面 | 当前可用性 | 阻断/前提 | 安全替代 | 能否在当前环境形成最终结论 |
|---|---|---|---|---|---|
| 待填写 | 待填写 | unknown | 待填写 | 待填写 | 待填写 |

结论：pending
"""


def next_task_id(tasks_dir: Path) -> str:
    day = datetime.now(timezone.utc).strftime("%Y%m%d")
    prefix = f"TASK-{day}-"
    nums = []
    for child in tasks_dir.glob(f"{prefix}*"):
        try:
            nums.append(int(child.name.rsplit("-", 1)[1]))
        except (IndexError, ValueError):
            pass
    return f"{prefix}{max(nums, default=0) + 1:03d}"


def create_task_dir(tasks_dir: Path) -> tuple[str, Path]:
    """Create a unique task directory even if another task starts concurrently."""
    for _ in range(999):
        task_id = next_task_id(tasks_dir)
        task_dir = tasks_dir / task_id
        try:
            task_dir.mkdir()
        except FileExistsError:
            continue
        return task_id, task_dir
    raise SystemExit("Could not allocate a unique task ID after 999 attempts")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", required=True)
    parser.add_argument("--task-type", choices=sorted(TYPES), required=True)
    parser.add_argument("--task-level", choices=sorted(LEVELS), required=True)
    args = parser.parse_args()

    root = Path(args.project_root).expanduser().resolve()
    if not root.is_dir():
        raise SystemExit(f"Project root does not exist: {root}")

    tasks_dir = root / ".hermes" / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    task_id, task_dir = create_task_dir(tasks_dir)
    (task_dir / "context-packets").mkdir()

    now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    status = f'''task_id: {task_id}
task_type: {args.task_type}
task_level: {args.task_level}
current_stage: project_identification
status: active
created_at: {now}
updated_at: {now}
current_branch: ""
contract_version: 0
approved_contract_version: null
verification_preflight: pending
delivery_reachability: unknown
limited_delivery_accepted_contract_version: null
retry_count: 0
blocking_issues: []
next_action: read_project_context
'''
    manifest = {
        "packet_version": 2,
        "allowed_paths": [],
        "protected_paths": [],
        "project_rules": [],
        "verified_commands": [],
        "prohibited_actions": [
            "git_push", "git_merge", "deploy", "production_database", "read_secrets",
        ],
        "notes": "Main controller must replace empty scope lists with verified project facts before delegation.",
    }
    (task_dir / "status.yaml").write_text(status, encoding="utf-8")
    (task_dir / "context-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    for filename in FILES:
        (task_dir / filename).write_text(f"# {filename}\n\n", encoding="utf-8")
    (task_dir / "test-plan.md").write_text(TEST_PLAN_TEMPLATE, encoding="utf-8")
    (task_dir / "verification-preflight.md").write_text(PREFLIGHT_TEMPLATE, encoding="utf-8")
    print(task_dir)


if __name__ == "__main__":
    main()
