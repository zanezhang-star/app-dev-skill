#!/usr/bin/env python3
"""Regression tests for app-dev context routing and process contracts."""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

APP_DEV = Path(__file__).resolve().parents[1]
INIT = APP_DEV / "scripts" / "init_task.py"
BUILD = APP_DEV / "scripts" / "build_context_packet.py"
ROLES = ("product", "architect", "developer", "quality")
MISSING = object()


class ContextPacketTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="app-dev-test-")
        self.project = Path(self.temp.name)
        self.run_command(["git", "init", "-b", "master"])
        self.run_command(["git", "config", "user.name", "Verifier"])
        self.run_command(["git", "config", "user.email", "verify@example.invalid"])
        (self.project / "README.md").write_text("v1\n", encoding="utf-8")
        self.run_command(["git", "add", "README.md"])
        self.run_command(["git", "commit", "-m", "init"])

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_command(
        self,
        command: list[str],
        expected: int = 0,
        *,
        cwd: Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(command, cwd=cwd or self.project, text=True, capture_output=True)
        self.assertEqual(
            result.returncode,
            expected,
            msg=f"command={command}\nstdout={result.stdout}\nstderr={result.stderr}",
        )
        return result

    def create_task(
        self,
        approved: bool = False,
        prepare_manifest: bool = True,
        complete_preflight: bool = True,
    ) -> Path:
        result = self.run_command([
            sys.executable, str(INIT), "--project-root", str(self.project),
            "--task-type", "feature", "--task-level", "medium",
        ])
        task = Path(result.stdout.strip())
        if prepare_manifest:
            self.write_manifest(task, ["README.md"])
        if approved:
            self.approve(task, complete_preflight=complete_preflight)
        return task

    def write_manifest(self, task: Path, allowed_paths: object = MISSING) -> None:
        data: dict[str, object] = {
            "packet_version": 1,
            "protected_paths": [],
            "project_rules": [],
            "verified_commands": [],
            "prohibited_actions": ["git_push", "read_secrets"],
            "notes": "test",
        }
        if allowed_paths is not MISSING:
            data["allowed_paths"] = allowed_paths
        (task / "context-manifest.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def approve(self, task: Path, *, complete_preflight: bool = True) -> None:
        path = task / "status.yaml"
        text = path.read_text(encoding="utf-8")
        text = text.replace("current_stage: project_identification", "current_stage: review_in_progress")
        text = text.replace("contract_version: 0", "contract_version: 1")
        text = text.replace("approved_contract_version: null", "approved_contract_version: 1")
        if complete_preflight:
            text = text.replace("verification_preflight: pending", "verification_preflight: complete")
            text = text.replace("delivery_reachability: unknown", "delivery_reachability: reachable_here")
        path.write_text(text, encoding="utf-8")

    def packet_command(
        self,
        task: Path,
        role: str,
        check: bool = False,
        runtime_root: Path | None = None,
    ) -> list[str]:
        command = [
            sys.executable, str(BUILD), "--project-root", str(self.project),
            "--task-id", task.name, "--role", role,
        ]
        if check:
            command.extend(["--check", "--runtime-root", str(runtime_root or self.project)])
        return command

    def test_initializer_artifact_schema(self) -> None:
        task = self.create_task(prepare_manifest=False)
        expected_files = {
            "request.md", "context.md", "plan.md", "acceptance.md", "test-plan.md",
            "development.md", "review.md", "test-report.md", "release-summary.md",
            "verification-preflight.md", "status.yaml", "context-manifest.json",
        }
        self.assertEqual({path.name for path in task.iterdir() if path.is_file()}, expected_files)
        self.assertTrue((task / "context-packets").is_dir())
        manifest = json.loads((task / "context-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["allowed_paths"], [])
        self.assertIsInstance(manifest["prohibited_actions"], list)
        status = (task / "status.yaml").read_text(encoding="utf-8")
        self.assertIn("contract_version: 0", status)
        self.assertIn("approved_contract_version: null", status)
        self.assertIn("verification_preflight: pending", status)
        self.assertIn("delivery_reachability: unknown", status)
        self.assertIn("limited_delivery_accepted_contract_version: null", status)
        test_plan = (task / "test-plan.md").read_text(encoding="utf-8")
        self.assertIn("合同驱动风险测试矩阵", test_plan)
        self.assertIn("跨入口一致性", test_plan)

    def test_allowed_paths_json_type_validation(self) -> None:
        task = self.create_task()
        invalid = [MISSING, None, [], "README.md", {}, [1], [True], [None], [""], ["README.md", 2]]
        for value in invalid:
            with self.subTest(value=value):
                self.write_manifest(task, value)
                result = self.run_command(self.packet_command(task, "product"), expected=1)
                self.assertIn("allowed_paths", result.stderr)
        for value in (["README.md"], ["0123", ".5", "1.", "1:20", "true", "null"]):
            with self.subTest(valid=value):
                self.write_manifest(task, value)
                self.run_command(self.packet_command(task, "product"))

    def test_four_role_packets_are_distinct_json_and_quality_isolated(self) -> None:
        task = self.create_task(approved=True)
        packets: dict[str, dict[str, object]] = {}
        raw_packets: list[str] = []
        for role in ROLES:
            output = self.run_command(self.packet_command(task, role))
            packet_path = Path(output.stdout.strip())
            self.assertEqual(packet_path.suffix, ".json")
            raw = packet_path.read_text(encoding="utf-8")
            raw_packets.append(raw)
            data = json.loads(raw)
            packets[role] = data
            self.assertEqual(data["common"]["status"], "active")
            for field in ("project_root", "git_toplevel", "git_common_dir", "git_dir"):
                self.assertIn(field, data["snapshot"])
            self.assertEqual(data["scope"]["boundary_kind"], "default_read_and_audit_scope_not_os_sandbox")
            self.assertIn("consumed_approved_contract_version", data["required_return_snapshot"])
            self.assertIn("consumed_project_root", data["required_return_snapshot"])
            self.assertIn("consumed_git_toplevel", data["required_return_snapshot"])
            self.assertIn("consumed_git_dir", data["required_return_snapshot"])
            self.assertIn("consumed_current_branch", data["required_return_snapshot"])
            self.assertTrue(data["runtime_identity_check"]["required_before_read_or_action"])
            self.assertEqual(data["runtime_identity_check"]["identity_mismatch_exit_code"], 3)
            self.assertEqual(data["runtime_identity_check"]["argv"][-2:], ["--runtime-root", "<ACTUAL_RUNTIME_ROOT>"])
            self.assertIsInstance(data["must_read"], list)
            self.assertIsInstance(data["may_read"], list)
            self.assertIsInstance(data["must_not_read"], list)
        self.assertEqual(len(set(raw_packets)), 4)
        self.assertFalse(any(path.endswith("plan.md") for path in packets["product"]["must_read"]))
        self.assertTrue(any(path.endswith("plan.md") for path in packets["developer"]["must_read"]))
        self.assertTrue(any(path.endswith("test-report.md") for path in packets["quality"]["must_read"]))
        self.assertTrue(any("developer completion claim" in item for item in packets["quality"]["must_not_read"]))
        self.assertFalse(any(path.endswith("development.md") for path in packets["quality"]["must_read"]))
        self.assertIn("Allowed when needed", packets["developer"]["may_read_expansion_policy"])
        self.assertTrue(any(path.endswith("verification-preflight.md") for path in packets["developer"]["must_read"]))

    def test_runtime_root_must_match_recorded_git_worktree_identity(self) -> None:
        task = self.create_task(approved=True)
        self.run_command(self.packet_command(task, "developer"))

        correct = self.run_command(
            [*self.packet_command(task, "developer", check=True), "--runtime-root", str(self.project)]
        )
        self.assertIn('"status": "FRESH"', correct.stdout)
        self.assertIn('"runtime_identity"', correct.stdout)

        missing = self.run_command(
            [sys.executable, str(BUILD), "--project-root", str(self.project), "--task-id", task.name, "--role", "developer", "--check"],
            expected=1,
        )
        self.assertIn("--check requires --runtime-root", missing.stderr)

        linked = self.project.parent / f"{self.project.name}-linked"
        self.run_command(["git", "worktree", "add", "-b", "linked-test", str(linked)])
        spoofed = self.run_command(
            [*self.packet_command(task, "developer", check=True), "--runtime-root", str(linked)],
            expected=1,
        )
        self.assertIn("must equal the checker process current working directory", spoofed.stderr)
        try:
            wrong = self.run_command(
                [*self.packet_command(task, "developer", check=True), "--runtime-root", str(linked)],
                expected=3,
                cwd=linked,
            )
            self.assertIn('"status": "IDENTITY_MISMATCH"', wrong.stdout)
            self.assertTrue("git_toplevel" in wrong.stdout or "git_dir" in wrong.stdout)
        finally:
            self.run_command(["git", "worktree", "remove", "--force", str(linked)])

        with tempfile.TemporaryDirectory(prefix="app-dev-wrong-repo-") as wrong_temp:
            wrong_repo = Path(wrong_temp)
            self.run_command(["git", "-C", str(wrong_repo), "init", "-b", "master"])
            self.run_command(["git", "-C", str(wrong_repo), "config", "user.name", "Verifier"])
            self.run_command(["git", "-C", str(wrong_repo), "config", "user.email", "verify@example.invalid"])
            (wrong_repo / "README.md").write_text("other\n", encoding="utf-8")
            self.run_command(["git", "-C", str(wrong_repo), "add", "README.md"])
            self.run_command(["git", "-C", str(wrong_repo), "commit", "-m", "other repo"])
            wrong = self.run_command(
                [*self.packet_command(task, "developer", check=True), "--runtime-root", str(wrong_repo)],
                expected=3,
                cwd=wrong_repo,
            )
            self.assertIn('"status": "IDENTITY_MISMATCH"', wrong.stdout)
            self.assertIn("git_common_dir", wrong.stdout)

    def test_developer_and_quality_require_completed_verification_preflight(self) -> None:
        task = self.create_task(approved=True, complete_preflight=False)
        for role in ("developer", "quality"):
            result = self.run_command(self.packet_command(task, role), expected=1)
            self.assertIn("verification preflight must be complete", result.stderr)

        status_path = task / "status.yaml"
        status = status_path.read_text(encoding="utf-8")
        status = status.replace("verification_preflight: pending", "verification_preflight: complete")
        status = status.replace("delivery_reachability: unknown", "delivery_reachability: external_required")
        status_path.write_text(status, encoding="utf-8")
        packet_path = Path(self.run_command(self.packet_command(task, "developer")).stdout.strip())
        packet = json.loads(packet_path.read_text(encoding="utf-8"))
        self.assertEqual(packet["common"]["delivery_reachability"], "external_required")

        (task / "verification-preflight.md").unlink()
        result = self.run_command(self.packet_command(task, "developer"), expected=1)
        self.assertIn("verification preflight artifact must exist", result.stderr)

    def test_not_reachable_requires_limited_delivery_acceptance(self) -> None:
        task = self.create_task(approved=True)
        status_path = task / "status.yaml"
        status = status_path.read_text(encoding="utf-8")
        status = status.replace("delivery_reachability: reachable_here", "delivery_reachability: not_reachable")
        status_path.write_text(status, encoding="utf-8")
        result = self.run_command(self.packet_command(task, "developer"), expected=1)
        self.assertIn("limited_delivery_accepted_contract_version", result.stderr)

        status_path.write_text(
            status.replace("limited_delivery_accepted_contract_version: null", "limited_delivery_accepted_contract_version: 1"),
            encoding="utf-8",
        )
        self.run_command(self.packet_command(task, "developer"))

    def test_contract_approval_gate(self) -> None:
        task = self.create_task()
        for role in ("developer", "quality"):
            result = self.run_command(self.packet_command(task, role), expected=1)
            self.assertIn("approved_contract_version == contract_version > 0", result.stderr)
        self.approve(task)
        path = task / "status.yaml"
        path.write_text(
            path.read_text(encoding="utf-8").replace(
                "approved_contract_version: 1", "approved_contract_version: 2"
            ),
            encoding="utf-8",
        )
        result = self.run_command(self.packet_command(task, "developer"), expected=1)
        self.assertIn("approved_contract_version == contract_version > 0", result.stderr)

    def assert_stale(self, task: Path, expected_key: str) -> None:
        result = self.run_command(self.packet_command(task, "quality", check=True), expected=2)
        self.assertIn('"status": "STALE"', result.stdout)
        self.assertIn(expected_key, result.stdout)

    def test_all_snapshot_dimensions_invalidate_packets(self) -> None:
        task = self.create_task(approved=True)
        status_path = task / "status.yaml"

        self.run_command(self.packet_command(task, "quality"))
        fresh = self.run_command(self.packet_command(task, "quality", check=True))
        self.assertIn('"status": "FRESH"', fresh.stdout)

        (self.project / "README.md").write_text("v2\n", encoding="utf-8")
        self.assert_stale(task, "worktree_fingerprint")
        self.run_command(["git", "checkout", "--", "README.md"])

        untracked = self.project / "new-file.txt"
        untracked.write_text("one\n", encoding="utf-8")
        self.run_command(self.packet_command(task, "quality"))
        untracked.write_text("longer content\n", encoding="utf-8")
        self.assert_stale(task, "worktree_fingerprint")
        untracked.unlink()

        mutations = [
            ("contract_version: 1", "contract_version: 2", "contract_version"),
            ("approved_contract_version: 1", "approved_contract_version: 2", "approved_contract_version"),
            ("updated_at:", "updated_at: 2099-01-01T00:00:00+00:00 #", "status_updated_at"),
            ("current_stage: review_in_progress", "current_stage: verification_in_progress", "current_stage"),
        ]
        for old, new, key in mutations:
            with self.subTest(snapshot=key):
                original = status_path.read_text(encoding="utf-8")
                self.run_command(self.packet_command(task, "quality"))
                status_path.write_text(original.replace(old, new), encoding="utf-8")
                self.assert_stale(task, key)
                status_path.write_text(original, encoding="utf-8")

        self.run_command(self.packet_command(task, "quality"))
        self.run_command(["git", "switch", "-c", "other"])
        self.assert_stale(task, "current_branch")
        self.run_command(["git", "switch", "master"])

        self.run_command(self.packet_command(task, "quality"))
        (self.project / "README.md").write_text("v3\n", encoding="utf-8")
        self.run_command(["git", "add", "README.md"])
        self.run_command(["git", "commit", "-m", "change head"])
        self.assert_stale(task, "git_head")

    def test_document_and_return_contract_consistency(self) -> None:
        skill = (APP_DEV / "SKILL.md").read_text(encoding="utf-8")
        references = set(re.findall(r"`(references/[A-Za-z0-9_./-]+\.md)`", skill))
        self.assertGreaterEqual(len(references), 6)
        for reference in references:
            self.assertTrue((APP_DEV / reference).is_file(), reference)
        self.assertIn("context-manifest.json", skill)
        self.assertIn("系统权限沙箱", skill)
        self.assertIn("may_read", skill)
        self.assertIn("唯一完整权威来源", skill)
        self.assertIn("不要一次性加载全部 references", skill)
        self.assertIn("普通项目交付不运行 `app-dev` 自身回归测试", skill)
        self.assertLessEqual(len(skill.encode("utf-8")), 10_000)
        for deferred_detail in (
            "worktree_fingerprint",
            "limited_delivery_accepted_contract_version",
            "每个任务最多一次",
        ):
            self.assertNotIn(deferred_detail, skill)

        role_files = [
            APP_DEV / "references" / "roles" / "product-analyst.md",
            APP_DEV / "references" / "roles" / "solution-architect.md",
            APP_DEV / "references" / "roles" / "developer.md",
            APP_DEV / "references" / "roles" / "quality-reviewer.md",
        ]
        for path in role_files:
            text = path.read_text(encoding="utf-8")
            for field in (
                "consumed_project_root", "consumed_git_toplevel", "consumed_git_common_dir",
                "consumed_git_dir", "consumed_current_branch", "consumed_git_head",
                "consumed_worktree_fingerprint", "consumed_contract_version",
                "consumed_approved_contract_version", "consumed_status_updated_at",
            ):
                self.assertIn(field, text, path.name)

        builder = BUILD.read_text(encoding="utf-8")
        self.assertIn("json.loads", builder)
        self.assertNotIn("yaml.safe_load", builder)
        self.assertIn('"consumed_approved_contract_version"', builder)

    def test_feedback_and_verification_policy_contracts(self) -> None:
        skill = (APP_DEV / "SKILL.md").read_text(encoding="utf-8")
        policy = (APP_DEV / "references" / "feedback-and-verification.md").read_text(encoding="utf-8")
        state = (APP_DEV / "references" / "task-state-machine.md").read_text(encoding="utf-8")
        routing = (APP_DEV / "references" / "task-routing-matrix.md").read_text(encoding="utf-8")

        self.assertIn("version: 0.3.3", skill)
        self.assertIn("真实观察优先", skill)
        self.assertIn("feedback-and-verification.md", skill)
        for header in ("输入条件", "内部状态", "用户可见状态", "可否重试", "是否允许默认值"):
            self.assertIn(header, policy)
        for phrase in (
            "real_world_validation_failed",
            "实现未满足既有、明确的 AC",
            "新增用户可见行为",
            "修改默认值、空值、未知值或回退语义",
            "确定性 RED 测试",
            "每个任务最多一次",
            "测试选择按**可执行代码和风险面变化**决定",
            "仅任务资料、文档、`status.yaml`",
        ):
            self.assertIn(phrase, policy)
        self.assertIn("ready_for_merge", state)
        self.assertIn("real_world_validation_failed", state)
        self.assertIn("Micro-review", state)
        self.assertIn("状态语义矩阵触发", routing)

        role_expectations = {
            "product-analyst.md": ("状态语义矩阵", "是否允许默认值"),
            "solution-architect.md": ("状态语义矩阵", "历史值压成零或实时值"),
            "developer.md": ("最小复现", "直接变化链"),
            "quality-reviewer.md": ("Micro-review 模式", "真实运行与状态语义"),
        }
        for filename, phrases in role_expectations.items():
            text = (APP_DEV / "references" / "roles" / filename).read_text(encoding="utf-8")
            for phrase in phrases:
                self.assertIn(phrase, text, filename)

    def test_preflight_and_contract_risk_matrix_document_contracts(self) -> None:
        skill = (APP_DEV / "SKILL.md").read_text(encoding="utf-8")
        policy = (APP_DEV / "references" / "verification-preflight-and-risk-matrix.md").read_text(encoding="utf-8")
        architect = (APP_DEV / "references" / "roles" / "solution-architect.md").read_text(encoding="utf-8")
        developer = (APP_DEV / "references" / "roles" / "developer.md").read_text(encoding="utf-8")
        quality = (APP_DEV / "references" / "roles" / "quality-reviewer.md").read_text(encoding="utf-8")

        self.assertIn("verification-preflight-and-risk-matrix.md", skill)
        self.assertIn("验证预检", skill)
        self.assertIn("风险维度", skill)
        for phrase in ("验证可行性预检", "delivery_reachability", "合同驱动风险测试矩阵"):
            self.assertIn(phrase, policy)
        for phrase in ("主路径", "边界/规模", "跨入口一致性", "权限/错误/状态", "所需证据"):
            self.assertIn(phrase, policy)
        self.assertIn("合同驱动风险测试矩阵", architect)
        self.assertIn("测试优先", developer)
        self.assertIn("风险测试矩阵", quality)

    def test_task_id_traversal_is_rejected(self) -> None:
        for task_id in ("../../escape", "TASK-20260802-001/../x", "TASK-20260802-1", "not-a-task"):
            with self.subTest(task_id=task_id):
                result = self.run_command([
                    sys.executable, str(BUILD), "--project-root", str(self.project),
                    "--task-id", task_id, "--role", "product",
                ], expected=1)
                self.assertIn("Invalid task ID", result.stderr)

    def test_concurrent_initialization_allocates_unique_ids(self) -> None:
        command = [
            sys.executable, str(INIT), "--project-root", str(self.project),
            "--task-type", "test", "--task-level", "small",
        ]
        processes = [
            subprocess.Popen(command, cwd=self.project, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            for _ in range(8)
        ]
        results = [process.communicate() for process in processes]
        self.assertTrue(all(process.returncode == 0 for process in processes), results)
        task_dirs = list((self.project / ".hermes" / "tasks").iterdir())
        self.assertEqual(len(task_dirs), 8)
        self.assertEqual(len({path.name for path in task_dirs}), 8)


if __name__ == "__main__":
    unittest.main(verbosity=2)
