---
name: app-dev
description: "Orchestrate safe, staged software delivery with role-scoped context."
version: 0.3.2
author: Hermes
metadata:
  hermes:
    tags: [Software, Development, Orchestration, Context, Testing, Review, Delivery]
---

# 通用软件交付编排器

`app-dev` 是跨技术栈的软件交付**唯一入口与总控**：识别任务和项目、维护任务状态、生成角色最小上下文包、按需调用角色、检查阶段产物，并控制授权、审查、测试和交付闸门。它不绑定具体项目、语言、数据库、业务规则或测试命令。

Product、Architect、Developer、Quality 是隔离角色，不共享完整聊天或全量项目上下文。项目知识保留在项目文档；单次证据保留在任务目录；总控只向每个角色提供公共最小事实和完成该角色工作所需的专属清单。

## 何时使用

- 用户要开发、修复、重构、调查、测试或交付软件功能。
- 用户要求可追踪、带角色隔离和真实验证的软件交付流程。
- 普通文本调用，例如：`请按 app-dev 的 plan 模式处理：<需求>`。

`/app-dev` 是提示词约定，不是 Hermes 内建 slash command。Gateway 会拦截未知命令时，先用 `/skill app-dev`，下一条再使用普通文本。

## 核心原则

1. **先识别，再修改。** 读取目标项目规则、Git 状态、技术栈、已有测试和禁改范围；目标不明确时停止并请用户指定。
2. **项目知识不进入通用 Skill。** 业务口径、数据字典、架构和历史决策放在目标项目；单次工作证据放在任务资料。
3. **最小上下文路由。** 禁止把完整对话、整个任务目录、全部项目文档或全仓库代码默认复制给每个角色。
4. **保留智能扩展。** `allowed_paths` 是默认读取与审计范围，不是操作系统权限沙箱。角色在信息不足时可按 `may_read` 扩展，但必须返回新增路径和原因；不得用越来越细的自然语言规则替代模型判断。
5. **子 Agent 返回结构化结果，主控负责落盘。** 主控核验角色快照、实际变更和测试证据后才写入任务文件和状态。
6. **事实与推测分离。** 缺少项目资料时记录未知项，不臆造业务规则或测试命令。
7. **不越权。** 不自动推送、合并、部署、迁移生产数据、提交密钥或清理无关变更。
8. **真实运行优先。** 用户在真实安装、数据、权限、UI 或外部集成中报告核心 AC 不满足时，受影响的交付结论立即失效；按 `references/feedback-and-verification.md` 重开任务并先建立最小复现。
9. **机器身份先于角色结论。** Agent 必须从 packet 记录的精确 Git worktree 通过运行时身份检查；错误仓库、worktree、分支、HEAD 或工作区结果一律拒绝采用。

## 前置检查

- 用 `terminal` 检查 Git 根目录、当前分支、HEAD、未提交变更和远程地址。
- 按 `references/verification-preflight-and-risk-matrix.md` 在开发授权前完成验证可行性预检，明确当前环境能否达到最终交付闸门。
- 用 `read_file` 读取存在的 `AGENTS.md`、`HERMES.md`、`CLAUDE.md`、`README.md`、`CONTRIBUTING.md` 及技术栈/测试配置。
- 只运行项目中已证实的构建、检查和测试命令；不得猜测或盲目安装依赖。
- 使用当前环境已验证的 Python 命令。Windows/Git Bash 通常为 `python`；Linux/macOS 可能为 `python3`。

## 任务资料与状态

运行：

```text
python <skill目录>/scripts/init_task.py --project-root <项目根目录> --task-type <类型> --task-level <等级>
```

在 `<项目根目录>/.hermes/tasks/<TASK-ID>/` 建立：

```text
request.md              原始需求与范围
context.md              已验证项目事实、限制与未知项
plan.md                 方案与影响分析
acceptance.md           编号、可检验的验收标准
test-plan.md            必须/建议/无法执行的测试
verification-preflight.md  开发前验证 Gate、环境可用性与交付可达性
development.md          实际变更与开发证据
review.md               独立质量审查结论
test-report.md          实际命令、结果与未执行原因
release-summary.md      面向交付的简要摘要
status.yaml             阶段、合同版本、阻塞项和下一步
context-manifest.json   公共范围、规则、命令与禁止动作（机器协议）
context-packets/        按角色生成的 JSON 最小读取清单
```

任务状态和合同版本见 `references/task-state-machine.md`。每次阶段迁移前重读 `status.yaml`，由主控更新阶段、版本、阻塞项、下一步和时间。发生真实运行反馈、复杂状态语义、合同/缺陷判定、第二轮后收敛或测试去重时，按需加载 `references/feedback-and-verification.md`；不要把该细节默认复制给无关角色。

## 上下文路由

执行任何委派前必须加载 `references/context-routing.md` 和对应角色协议。公共与角色模板位于 `references/context-packets/`。

机器读取的 manifest 和角色 packet 使用 JSON，由 Python 标准库严格解析。Markdown 保留需求、方案、AC、Review 等自然语言内容，不把机器类型约束扩散到角色写作。

生成角色清单：

```text
python <skill目录>/scripts/build_context_packet.py --project-root <项目根目录> --task-id <TASK-ID> --role <product|architect|developer|quality>
```

角色开始读取或执行前，必须在其**实际运行目录作为进程 cwd** 执行机器身份检查；`--runtime-root` 必须与该 cwd 相同，不能从其他目录伪报路径：

```text
python <skill目录>/scripts/build_context_packet.py --project-root <项目根目录> --task-id <TASK-ID> --role <角色> --check --runtime-root <Agent实际工作目录>
```

退出码 `3` 的 `IDENTITY_MISMATCH` 表示错误仓库、linked worktree、分支、HEAD 或工作区；该角色不得继续，主控不得采用其结果。

总控传给子 Agent 的初始内容仅包括：

- 角色目标；
- 公共最小事实；
- 生成的 JSON 上下文包绝对路径；
- `must_read` 路径；
- 关键 `must_not_read` 和禁止动作。

其余内容由角色遵循 `may_read` 按需检索。先搜索再局部读取，大文件和日志通过路径引用，不内联完整正文。扩展读取不是违规，但必须与当前角色目标直接相关并记录路径和原因。

### 版本与过期闸门

上下文包记录规范化 `project_root`、`git_toplevel`、`git_common_dir`、`git_dir`，以及 `git_head`、`current_branch`、`worktree_fingerprint`、`contract_version`、`approved_contract_version` 和 `status_updated_at`。Git dir 区分同仓库的 linked worktree；工作区指纹覆盖当前 tracked diff 及非 `.hermes/` 未跟踪文件元数据。

任何角色 `must_read` 文件、JSON 清单、批准合同或测试/diff 证据变化时，主控必须先更新 `status.updated_at`；生成包本身不更新时间。角色返回必须声明实际使用的快照。主控采用结果前重新核对；任一关键值变化则标记 `stale`，不得直接采用，必须重新生成包并重新委派或局部复核。

Developer 和 Quality 仅在 `approved_contract_version == contract_version > 0`、`verification_preflight: complete` 且预检资料存在时可获得可执行上下文包。`delivery_reachability: external_required` 可在用户知情授权后开发，但不得伪报当前环境可以完成最终验证；`not_reachable` 还要求当前合同版本的 `limited_delivery_accepted_contract_version` 明确记录受限交付接受。旧任务升级后必须补齐预检文件和三个状态字段，再生成新 packet。需求或合同变化时先增加 `contract_version`，把任务退回分析/确认阶段；用户重新确认后再同步批准版本。

## 任务路由与角色

先按风险和范围分为 small / medium / large，再按 `references/task-routing-matrix.md` 选择角色。不要为了“多 Agent”让每个任务经过全套角色。

- Product：`references/roles/product-analyst.md`
- Architect：`references/roles/solution-architect.md`
- Developer：`references/roles/developer.md`
- Quality：`references/roles/quality-reviewer.md`

大型报表、运营管理、权限、周期名单或 Excel 功能，在方案审查前还须加载 `references/large-business-plan-preflight.md`。

## 执行流程

1. **识别与分级。** 记录需求、项目、限制、禁改范围、Git 快照和任务等级；初始化任务资料和 `context-manifest.json`。
2. **Product 分析。** medium/large 生成 Product 包并委派只读分析；small 仅在需求不清时使用。主控核验快照后写入需求、AC、待决项和测试草案。
3. **Architect 方案。** 每个 large 任务必须调用；medium 仅在架构、数据模型、权限、外部系统、采集/RPA 等风险出现时调用。主控核验后写入方案和测试计划。
4. **验证预检与风险矩阵。** 在授权开发前完成 `verification-preflight.md`，把 Gate 可用性写入状态；同时由合同推导 `test-plan.md` 的主路径、边界/规模、跨入口一致性、权限/错误/状态和所需证据。只选择适用维度，不为填表制造测试。
5. **固定合同并等待授权。** 每次合同实质变化增加 `contract_version`；实现未满足已唯一确定的 AC 属于 defect，不增加版本。方案、验证可达性和主要风险可确认时进入 `awaiting_approval`；用户明确授权后设置批准版本。
6. **隔离开发。** Developer 先从实际目录通过 `--check --runtime-root`，再读取批准合同和风险矩阵，按测试优先完成最小改动。主控核验身份、快照、diff、变更面与 AC 后写入 `development.md`。
7. **独立审查与测试。** Quality 使用新的包并先通过运行时身份检查；读取原始需求、批准合同、风险矩阵、实际 scoped diff、当前代码和原始测试输出，**不得接收 Developer 主观自评或主控预设结论**。
8. **问题闭环。** `BLOCKER` 必须修；`MAJOR` 原则上修，除非用户接受风险。默认最多两轮完整“定向修复 → 新包 → 独立复审”。第二轮仅剩范围受限、确定性 RED→GREEN、无高风险副作用的问题时，可执行一次独立 micro-review。
9. **交付与真实反馈。** 全部 AC 有证据、预检要求的必须 Gate 已真实执行、无未接受阻断问题且 diff/文档检查通过，才可标为 `ready_for_merge`。真实观察与核心 AC 冲突时旧结论立即失效。

## 验收与测试硬规则

- AC 使用唯一编号，包含前置条件、操作、预期结果及必要的数据/权限预期。
- 未确认的数据键、周期、权限、唯一约束必须进入 `blocking_issues`，不能写成动态占位 AC。
- 构建成功、HTTP 200、页面可打开或开发者自述都不等于需求验收。
- `test-report.md` 记录命令、环境、范围、对应 AC、退出码、结果和未执行原因。
- 委派结果未返回、快照过期或未被主控核验时，不得报告 PASS。
- 多来源、多阶段、降级、默认/空/零/历史/权限/可重试错误存在时，合同必须包含状态语义矩阵：输入条件、内部状态、用户可见状态、可否重试、是否允许默认值。
- 合同驱动风险测试矩阵由 AC 推导；按风险选择主路径、边界/规模、跨入口一致性、权限/错误/状态和证据层级，不把重复测试次数当覆盖质量。
- 测试选择遵循“变更链优先、阶段闸门广测一次”：任务资料/文档/状态变化只做结构、diff 和 freshness；测试变化跑受影响测试；业务代码变化跑 focused test 与依赖链；Quality 或提交闸门再跑一次约定广测试。

## Git 与远程规则

- 远程含 `gitee.com` 时识别为 Gitee，但本地仍用标准 Git；不调用 GitHub 专属 CLI/API。
- 未获明确授权时，不执行 push、创建远程分支/标签/合并请求、合并或部署。
- 用户明确要求远程写入后，先报告远程、目标分支、变更范围和测试结果；分支策略服从本次授权、项目规则与既定协作约定。
- 提交前检查状态、`git diff --check` 和 scoped diff/stat，只暂存本任务文件。

## 降级与验证

若无法使用 `delegate_task`，明确说明，并在单 Agent 中按角色分段；每段只读取对应上下文包，重读任务状态和当前 diff，不得用前一角色的主观结论替代独立证据。

完成后至少执行项目已有测试及本 Skill 的回归测试：

```text
python <skill目录>/tests/test_context_packets.py -v
```

并验证 JSON 包可解析、角色清单存在差异、快照过期会被拒绝、任务资料同步、`git diff --check` 通过且状态与阶段一致。
