# Standard 轻量上下文路由

仅在 Standard Lane 实际委派角色时读取。单 Agent 任务只使用工作笔记或 `task-brief.md`，不生成 Packet。

## 边界

轻量 Packet 用于区分角色目标和读取范围，不启用 Controlled 的状态机、合同版本、完整 worktree fingerprint 或 runtime identity check。任一风险升级信号出现时停止使用轻量协议，升级 Controlled。

轻量包必须包含：

- 角色目标与预期输出；
- `task-brief.md` 和角色必读路径；
- `may_read`、`must_not_read` 与 scoped paths；
- 项目根、分支、HEAD、task brief 哈希和生成时间；
- 禁止动作与回收时必须声明的最小快照。

## 生成

先填写 `assets/task-brief.md` 的委派行，再只为会运行的角色生成 JSON：

```text
python <skill>/scripts/build_standard_packet.py \
  --project-root <root> \
  --task-brief <root内的task-brief.md> \
  --role <product|architect|developer|quality> \
  --role-goal "<该角色唯一目标>" \
  --scope-path <相关路径> \
  --must-read <必读文件> \
  --may-read "<信息不足时允许扩展的内容>" \
  --must-not-read "<默认禁止内容>" \
  --expected-output "<结构化交付>"
```

`--scope-path`、`--must-read`、`--may-read` 和 `--must-not-read` 可重复。输出默认位于 task brief 同目录的 `context-packets/<role>.json`。

## 使用与回收

委派时只内联角色目标、Packet 绝对路径和关键禁止事项，不传完整聊天。角色先读 `must_read`，信息不足时才扩展 `may_read` 并返回新增路径与理由。

回收结果前检查轻量快照：

```text
python <skill>/scripts/build_standard_packet.py \
  --project-root <root> --task-brief <task-brief.md> --role <role> --check
```

HEAD、分支、项目根或 task brief 哈希变化时结果为 `STALE`；重新生成并局部复核。轻量检查不证明 worktree、合同或运行身份完整一致，高风险任务必须升级 Controlled。

Quality 不接收 Developer 主观自评；只读取任务目标、验收条件、实际 diff/代码和原始验证证据。`allowed_paths` 是默认读取与审计范围，不是操作系统权限沙箱。
