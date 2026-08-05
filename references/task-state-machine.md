# App-Dev 任务状态机

`status.yaml` 是任务当前事实的唯一入口。主控在每次阶段切换、合同变化、真实运行反馈和结果回收前重读它，并在核验角色快照与实际工具证据后更新。

## 必填字段

```yaml
task_id: TASK-YYYYMMDD-NNN
task_type: feature | fix | refactor | performance | security | test | documentation | configuration | investigation
task_level: small | medium | large
current_stage: <下列阶段之一>
status: active | awaiting_approval | blocked | ready_for_merge
created_at: <UTC ISO-8601>
updated_at: <UTC ISO-8601>
current_branch: <已验证分支>
contract_version: 0
approved_contract_version: null
verification_preflight: pending
delivery_reachability: unknown
limited_delivery_accepted_contract_version: null
retry_count: 0
blocking_issues: []
next_action: <可执行的下一步>
```

## 合同版本

- 新任务从 `contract_version: 0` 开始。
- Product/Architect 形成第一份可确认合同，或需求/AC/方案发生实质变化时，将 `contract_version` 增加 1。
- 用户明确授权当前合同进入开发时，将 `approved_contract_version` 设置为当前 `contract_version`。
- 合同再次变化时立即进入分析或等待确认；旧的批准版本不得授权新开发。
- Developer/Quality 仅在 `contract_version > 0`、`approved_contract_version == contract_version`、`verification_preflight: complete` 且 `verification-preflight.md` 存在非空内容时可执行。`delivery_reachability` 必须是 `reachable_here`、`external_required` 或 `not_reachable`；当其为 `not_reachable` 时，`limited_delivery_accepted_contract_version` 必须等于当前合同版本。

先问“预期行为是否已被当前批准合同唯一确定”：

| 变化 | 是否增加合同版本 |
|---|---|
| 实现未满足既有明确 AC | 否，按 defect 修复并记录复现/证据 |
| 与既有 AC 一致的边界修复 | 否 |
| 新增用户可见行为 | 是 |
| 修改默认值、空值、未知值或回退语义 | 是 |
| 改变安全、权限、数据保留、删除、唯一性或计费语义 | 是 |
| 原合同沉默/含糊，用户首次确定产品语义 | 是 |
| 只补充复现、测试证据或不改变行为的说明 | 否 |

完整判断见 `feedback-and-verification.md`。不升级合同不等于不留痕；defect 仍必须关联受影响 AC、最小复现、修复 diff 和复测结果。

## 阶段与状态对应

`current_stage` 描述流程位置，`status` 描述任务是否可继续；两者必须同时更新。`status: active` 不表示已获开发授权。

| `current_stage` | 允许的 `status` | 合同约束 |
|---|---|---|
| `project_identification` / `context_ready` / `analysis_in_progress` | `active` | 批准版本可为空或落后于当前版本 |
| `awaiting_approval` | `awaiting_approval` | `contract_version > 0`，批准版本为空或落后 |
| `development_in_progress` / `review_in_progress` / `verification_in_progress` | `active` | `approved_contract_version == contract_version > 0` |
| 任一阶段 | `blocked` | `blocking_issues` 非空，`next_action` 说明需要的决定或输入 |
| `ready_for_merge` | `ready_for_merge` | 批准版本等于当前版本，交付闸门通过 |

## 阶段与迁移

| 当前阶段 | 允许进入 | 进入条件 | 主控必须落盘 |
|---|---|---|---|
| `project_identification` | `context_ready` | 已确认项目、规则、Git 状态和任务等级 | `context.md`、`context-manifest.json`、`status.yaml` |
| `context_ready` | `analysis_in_progress` / `development_in_progress` | small 且已有批准合同可直接开发；medium/large 先分析 | 分级依据、路由选择 |
| `analysis_in_progress` | `awaiting_approval` / `blocked` | Product/Architect 结果快照有效；关键规则已锁定；合同版本已增加 | `plan.md`、`acceptance.md`、`test-plan.md` |
| `awaiting_approval` | `development_in_progress` / `analysis_in_progress` | 验证预检完成、预检资料存在、可达性已告知用户且用户明确授权当前版本；`not_reachable` 时还需受限交付接受版本等于当前合同；若需求变化则增加版本并回分析 | 授权证据、批准版本、`verification-preflight.md`、受限交付接受版本或变更原因 |
| `development_in_progress` | `review_in_progress` / `blocked` | Developer 快照有效，实际 diff 与 AC 已核验 | `development.md` |
| `review_in_progress` | `verification_in_progress` / `development_in_progress` / `blocked` | Quality 快照有效并已落盘；BLOCKER/MAJOR 需修复 | `review.md`、问题清单 |
| `verification_in_progress` | `ready_for_merge` / `development_in_progress` / `analysis_in_progress` / `blocked` | 必须测试有真实结果，AC 均有证据；真实反馈按语义选择开发或分析 | `test-report.md`、`release-summary.md`、失败证据 |
| `ready_for_merge` | `analysis_in_progress` / `development_in_progress` | 新范围/新语义增加合同版本并回分析；既有 AC defect 或真实运行失败回开发 | 新合同或 `real_world_validation_failed` 修复记录 |

### 真实运行验收重开

真实安装、真实数据、真实权限、真实 UI、真实 CLI、迁移或第三方集成的观察若与核心 AC 冲突：

- 受影响的 `ready_for_merge`、verification 和 Quality 结论立即失效；不相关历史证据可保留但不能覆盖失败。
- 任务记录 `real_world_validation_failed`，包括环境、输入、观察、受影响 AC 和证据。
- 既有明确 AC 未满足：合同不变，进入 `development_in_progress`；暴露新/含糊语义：增加合同版本，进入 `analysis_in_progress`。
- 先建立最小复现，修复后重新执行直接变化链和真实环境验收；不能用此前自动化 PASS 代替。

## 上下文快照检查

每个角色 JSON 包与返回结果至少带回：规范化项目根、Git toplevel/common dir/worktree git dir、当前分支、Git HEAD、工作区指纹、合同版本、批准合同版本和状态更新时间。角色必须先从实际目录通过 `--check --runtime-root`。主控回收结果时重新读取 `status.yaml` 并重新计算 Git/工作区快照：

- Product/Architect：Git HEAD、工作区指纹、合同版本或阶段不匹配时标记 `stale`。
- Developer/Quality：上述值及批准合同版本任一不匹配时标记 `stale`。
- 任何角色 `must_read` 文件、`context-manifest.json`、批准合同或测试/diff 证据变化时，主控必须先更新 `updated_at`；生成 JSON 包本身不更新时间。
- `stale` 结果不能更新当前结论，只能作为线索；必须重新生成包并重新委派或局部复核。

## 两轮收敛与 Micro-review

- `BLOCKER` 必须修复；未接受的 `MAJOR` 必须回开发。
- 默认最多两轮完整定向修复和独立复审；第二轮仍有普通 BLOCKER/MAJOR 时标记 `blocked`。
- 只有当第二轮剩余问题无范围扩张、修改面受限、有确定性 RED→GREEN，且不涉及安全、权限、不可逆数据、生产迁移、计费或外部副作用时，可执行一次独立 micro-review。
- Micro-review 只读 issue、受影响 AC 摘要、相关 diff/代码和原始测试证据；它与 Developer 隔离，并与第二轮未受影响结论组合形成最终闸门。
- 每个任务最多一次；条件不满足、证据过期、范围扩大或 micro-review 失败时立即 `blocked`。用户明确授权的其他例外轮次必须单独记录，不能伪装成 micro-review。

## 其他约束

- `awaiting_approval` 不是开发授权。
- 委派结果未返回、实际测试证据缺失、包已过期或待决规则存在时，不得推进。
- 测试按风险面选择：仅任务资料/状态变化不重跑应用测试；业务代码跑直接变化链；独立 Quality 或提交闸门在同一源码快照上只跑一次约定广测试。
- `ready_for_merge` 只表示本地交付闸门通过，不代表允许提交、推送、合并、发布或生产变更。
