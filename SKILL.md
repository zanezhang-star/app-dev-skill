---
name: app-dev
description: "按风险分流并实施软件功能开发、修复、重构、测试和本地交付。用于需要实际修改仓库的任务；明确、局部、低风险变更默认走 Fast Lane，只有范围不清、跨模块、数据、权限、安全、基础设施或外部集成风险才升级。不要用于仅解释代码、概念问答或不要求修改的一次性建议。"
---

# App Dev

用与风险相称的最小流程交付可验证的软件变更。

## 底线

- 先确认目标仓库，再检查项目规则、Git 状态、相关实现和已有测试。
- 保留用户的无关改动；未获授权，不推送、合并、部署、迁移生产数据、提交密钥或执行破坏性操作。
- 不猜业务语义，不用自述、构建成功、HTTP 200 或页面可打开冒充需求验收。
- 只读取任务相关的文件和输出；不得默认加载全部 references、项目文档、日志或全量 diff。
- 真实代码、diff、命令退出码和可复现结果优先。

## 选择执行通道

根据已观察到的范围选择通道。通道不明确或出现升级信号时，才读取 `references/task-routing-matrix.md`。

### Fast Lane（默认）

适用于需求明确、修改局部、容易回滚，且不涉及数据库迁移、权限/安全边界、外部集成、基础设施或广泛行为变化的任务。

1. 定位最小相关代码和测试面。
2. 当前 Agent 直接实现；默认不初始化 `.hermes`、不生成 Context Packet、不调用 Product、Architect 或独立 Quality。
3. 运行最窄但有意义的测试；存在 Git 时运行 `git diff --check`。
4. 审查 scoped diff 是否满足需求、引入回归或夹带无关修改。
5. 汇报改动文件、验证证据和未验证限制。

只有缺失决定会实质改变实现时才阻断提问；否则采用安全且明确说明的假设继续。

### Standard Lane

适用于需求基本明确但跨多个文件/模块、增加接口或配置、或有明显回归风险且不触及高风险边界的任务。

- 默认仍由当前 Agent 连续完成，不为形式拆分角色。
- 用简短工作笔记维护验收条件和测试计划；需要跨会话、交接或持久记录时，复制并填写 `assets/task-brief.md`，否则不要仅为流程完整创建文件。
- 仅在需求语义未定时调用 Product；仅在关键设计取舍时调用 Architect；仅在独立审查能显著增信时调用 Quality。
- 单 Agent 不生成 Packet；发生角色委派时，读取 `references/standard-context-routing.md` 并只为实际角色生成 lightweight Packet。
- 包含当前 Agent 在内最多使用 3 个角色。
- 运行 focused tests 和覆盖直接依赖链的最小广测。

### Controlled Lane

适用于数据库/迁移、认证授权、敏感数据、外部 API、基础设施、破坏性操作、跨项目依赖或大型不确定任务。

开发授权前完成验证预检，并从批准合同选择适用风险维度、推导必须执行的 Gate；无法到达的验证环境必须明确限制和交接责任。

只为下一步读取所需协议：

- 生命周期和批准：`references/task-state-machine.md`
- 委派、身份和 freshness：`references/context-routing.md`
- 验证设计：`references/verification-preflight-and-risk-matrix.md`
- 反馈和缺陷闭环：`references/feedback-and-verification.md`
- 大型业务流程：`references/large-business-plan-preflight.md`
- 某角色即将执行时：`references/roles/<role>.md`

确认项目后，仅在需要追踪合同或委派时初始化任务：

```text
python <skill>/scripts/init_task.py --project-root <root> --task-type <type> --task-level <medium|large>
```

只为实际会运行的角色生成 Packet：

```text
python <skill>/scripts/build_context_packet.py --project-root <root> --task-id <TASK-ID> --role <role>
```

委派前按 `references/context-routing.md` 执行 runtime identity check；身份不匹配或证据过期时停止采用结果。

## 成本与升级闸门

| 通道 | 默认资料 | 角色预算 | 验证 |
|---|---|---:|---|
| Fast | 不建档 | 1 | focused test + scoped review |
| Standard | 简短工作笔记 | 最多 3 | focused + 最小相关广测 |
| Controlled | 按需 `.hermes` | 风险所需 | 合同和风险驱动 Gate |

范围扩大或证据揭示新风险时立即升级；保留已完成证据，只补新增必要步骤。不得为了省流程而降级，也不得在风险未变化时反复重新分级。

测试、Review、AC 或真实运行失败时，读取 `references/diagnosis-matrix.md`；先锁定失败维度和最小复现，只修受影响部分，再按直接变化链重测。不要无诊断地整段重写或重复全量流程。

## 完成

当请求行为已实现、scoped diff 已理解、相称检查通过或限制已明确、且无未接受阻断时完成本地交付。“本地完成”不代表已获提交、推送、合并、发布或生产修改授权。

只有修改本 Skill 的脚本、Packet schema、模板或协议时，才运行自身回归：

```text
python <skill>/tests/test_context_packets.py -v
```
