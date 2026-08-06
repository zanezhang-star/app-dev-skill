---
name: app-dev
description: "Orchestrate safe, staged software delivery with role-scoped context."
version: 0.3.3
author: Hermes
metadata:
  hermes:
    tags: [Software, Development, Orchestration, Context, Testing, Review, Delivery]
---

# 通用软件交付编排器

## 概述与使用边界

`app-dev` 是跨技术栈的软件交付总控：识别项目和任务、按风险分级、维护状态、按需调用隔离角色，并以真实代码、diff、测试和运行证据控制开发、审查与交付。它不绑定具体项目、语言、业务规则或测试命令。

用于开发、修复、重构、调查、测试或交付软件功能，尤其适合需要可追踪合同、角色隔离和真实验证的任务。不适用于只解释概念或代码、只需一次性文字建议、目标项目尚未确认的场景；未确认项目时不得创建任务资料或修改代码。

Product、Architect、Developer、Quality 不共享完整聊天或全量项目上下文。项目知识留在项目文档，单次证据留在任务目录；总控只提供公共最小事实和角色所需清单。

## 全局底线

1. **先识别，再修改。** 先确认目标项目、项目规则、Git 状态、已有测试和禁改范围。
2. **事实分层。** 项目事实留在项目，任务证据留在 `.hermes/tasks/`，通用 Skill 不吸收项目特例。
3. **最小上下文。** 不把完整对话、整个任务目录、全部项目文档或全仓库代码默认复制给角色。
4. **少量硬校验。** 机器校验身份、版本和可执行前提；自然语言方案、检索和风险判断保留智能扩展。
5. **不猜、不虚报。** 未知业务语义、命令、权限和验证能力进入阻断或交接项；角色结论须由主控用当前状态、diff、代码和原始证据核验。
6. **不越权。** 未获明确授权，不推送、合并、发布、部署、迁移生产数据、提交密钥或清理无关变更。
7. **真实观察优先。** 真实安装、数据、权限、UI、CLI 或外部集成与核心 AC 冲突时，受影响结论立即失效。

## 协议权威与加载路由

主文档只负责总控决策。详细规则以下列 reference 为唯一完整权威来源；不要一次性加载全部 references。

| 主题 | 权威来源 | 何时加载 |
|---|---|---|
| 任务等级与角色选择 | `references/task-routing-matrix.md` | 分级或范围变化时 |
| 阶段、状态、合同版本和迁移 | `references/task-state-machine.md` | 初始化、推进阶段或合同变化时 |
| Packet、身份、freshness、角色隔离 | `references/context-routing.md` | 本任务首次委派前；协议或相关状态变化后重读 |
| 验证可达性与风险测试 | `references/verification-preflight-and-risk-matrix.md` | 固定合同并授权开发前 |
| 真实反馈、复杂状态、合同/缺陷、micro-review、测试去重 | `references/feedback-and-verification.md` | 出现对应触发条件时 |
| 大型业务方案预检 | `references/large-business-plan-preflight.md` | 大型报表、运营、权限、周期名单或 Excel 方案审查前 |
| 角色职责与输出 | `references/roles/*.md` | 准备调用对应角色时 |

冲突时依次采用：用户本次要求、项目规则、当前批准合同、当前代码与实际证据、通用最佳实践。

## 前置发现与任务初始化

创建任务或修改代码前：

- 确认 Git 根、分支、HEAD、未提交变更和远程；
- 读取存在的项目规则、README、贡献说明及技术栈/测试配置；
- 搜索相关实现和测试，只局部读取与任务有关的内容；
- 只采用项目中已证实的命令，不盲目安装依赖；
- 按路由矩阵判断 small / medium / large，范围扩大时重新分级。

完成标准：项目、规则来源、范围、等级、Git 快照、验证能力和未知项明确；目标或关键语义不明时停止修改并请求决定。

确认项目后初始化任务：

```text
python <skill目录>/scripts/init_task.py --project-root <项目根目录> --task-type <类型> --task-level <等级>
```

任务资料位于 `<项目根目录>/.hermes/tasks/<TASK-ID>/`，保存需求、上下文、方案、AC、测试计划、预检、开发/审查/测试证据、交付摘要、`status.yaml`、`context-manifest.json` 和角色 packets。字段与迁移以状态机为准；阶段迁移、合同变化、真实反馈和结果回收前重读 `status.yaml`，只由主控在核验证据后更新。

## 阶段路由

| 阶段 | 进入条件 | 加载内容 | 完成标准 |
|---|---|---|---|
| 识别与分级 | 所有任务 | 路由矩阵 | 项目、范围、等级、限制明确 |
| Product | medium/large；small 仅在需求不清时 | Product 协议 | AC、边界、待决项明确 |
| Architect | large；高风险 medium | Architect 协议；必要时大型业务预检 | 方案、影响面、风险可审查 |
| 验证预检 | 所有开发任务 | 预检与风险矩阵 | 必需 Gate、证据层级、可达性明确 |
| 固定合同 | 方案和验证边界可确认 | 状态机 | 当前合同获明确开发授权 |
| Developer | 合同已批准且预检满足条件 | 上下文路由、Developer 协议 | 最小实现和直接变化链证据已核验 |
| Quality | scoped diff 已核验 | Quality 协议 | 合同、代码风险和测试真实性有独立结论 |
| 闭环/交付 | 出现问题或 AC 证据齐备 | 触发时加载反馈协议 | 问题已修复/阻断，或达到本地交付闸门 |

不要为了多 Agent 强制全角色流水线；按路由矩阵和实际风险决定调用或升级。

## Context Packet 与委派

本任务首次委派前加载 `context-routing.md` 和对应角色协议；身份协议、合同、状态结构或相关证据变化后重读并生成新包。

```text
python <skill目录>/scripts/build_context_packet.py --project-root <项目根目录> --task-id <TASK-ID> --role <product|architect|developer|quality>
```

角色开始前，必须从其实际进程工作目录运行：

```text
python <skill目录>/scripts/build_context_packet.py --project-root <项目根目录> --task-id <TASK-ID> --role <角色> --check --runtime-root <Agent实际工作目录>
```

检查失败时立即停止，主控不得采用其结论。身份字段、指纹、合同前提、过期判定和结果回收以 `context-routing.md` 为准。

初始只传角色目标、公共最小事实、Packet 绝对路径、`must_read` 及关键禁止事项。角色按 `may_read` 搜索后局部扩展并记录路径与理由；大型日志、完整 diff 和项目文档只传路径。`allowed_paths` 是默认读取与审计范围，不是假装存在的系统权限沙箱。

Quality 独立读取原始需求、批准合同、实际 diff、当前代码和原始测试证据，不接收 Developer 主观自评或主控预设结论。

## 合同、验证与测试

- AC 使用唯一编号且可检验；未确认的关键业务语义不能写成占位 AC。
- 授权开发前完成验证预检，并从 AC 推导适用风险维度；不为填表制造测试。
- 构建成功、HTTP 200、页面可打开或开发者自述不等于需求验收。
- 业务代码变化先跑 focused test 和直接依赖链；独立 Quality 或提交闸门在同一源码快照上运行一次项目约定广测试。
- 无法执行的 Gate 必须说明能证明什么、不能证明什么及交接责任；弱证据不得冒充真实环境证据。
- 合同变化、defect、复杂状态、真实反馈和复审收敛只在触发时按反馈协议处理。

## 完成与交付

只有当前合同与状态/代码/Packet 一致、每个 AC 有相称证据、必须 Gate 已执行或限制已明确接受、无未接受阻断、scoped diff 与任务资料一致，并通过 `git diff --check` 及项目适用最终检查，才可标记 `ready_for_merge`。

`ready_for_merge` 只表示本地交付闸门通过，不代表已获提交、推送、合并、发布、部署或生产变更授权。用户要求远程写入后，再按本次授权、项目规则和相应 Git 工作流核对远程、分支、diff、测试与暂存范围。

## 降级、Skill 自检与误区

无法使用 `delegate_task` 时，明确说明并在单 Agent 中按角色分段；每段只读对应 Packet，重读当前状态和 diff，不以前一角色的主观结论替代独立证据。

普通项目交付不运行 `app-dev` 自身回归测试。只有修改本 Skill 的脚本、Packet、状态协议、模板或总控规则时才运行：

```text
python <skill目录>/tests/test_context_packets.py -v
```

并验证 JSON、角色差异、身份/过期拒绝、任务资料同步和状态一致性。目标项目始终按自身合同、风险和已证实命令验证。

避免：未确认项目就建档或改代码；为 small 任务机械调用全角色；提前加载全部 references；在主文档和 reference 维护两套完整协议；用构建、Mock、旧测试或自评冒充 AC 证据；因任务文档更新重复跑全量测试；把 `ready_for_merge` 误报成远程或生产授权。
