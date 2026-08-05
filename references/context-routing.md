# 上下文路由协议

目标：让多个角色共享同一组权威事实，但只读取完成本角色任务所需的最小内容。禁止把完整对话、整个任务目录、全部项目文档或全仓库代码默认复制给每个 Agent。

## 1. 权威来源优先级

发生冲突时依次采用：

1. 用户本次明确要求；
2. 项目规则文件（AGENTS.md、HERMES.md、CLAUDE.md 等）；
3. 当前 `approved_contract_version` 对应的 `plan.md`、`acceptance.md`、`test-plan.md`；
4. 当前 Git HEAD 的代码、配置和实际 diff；
5. 通用最佳实践。

`request.md` 保留原始意图；批准合同负责固定可开发、可测试的唯一口径。任何合同变化必须增加 `contract_version`，重新确认后同步 `approved_contract_version`。

## 2. 三层上下文

### 公共最小事实包

所有角色只共享：任务 ID/类型/等级/阶段、规范化项目根、Git toplevel/common dir/worktree git dir、HEAD/分支/脏文件摘要、合同版本、批准合同版本、验证预检/交付可达性、状态更新时间、默认/保护路径、项目规则路径、已验证命令和禁止动作。公共包不内联大型正文。

### 角色专属清单

每个角色必须具有：

- `must_read`：开始工作前必须读取；
- `may_read`：信息不足时可按需扩展，并记录新增路径和原因；
- `must_not_read`：默认禁止输入或主动读取；
- `evidence_policy`：允许采用的证据类型；
- `output_contract`：结构化返回要求。

### 按需检索

先搜索符号、路径或标题，再读取相关区间。大文件、完整日志和大 diff 通过路径引用；只在必要时读取相关片段。不得先全仓库扫描再决定任务范围。

`allowed_paths` 是**默认读取与审计边界**，不是操作系统权限沙箱。角色因完成当前职责需要扩展 May Read 时，可以读取额外相关内容，但必须在结果中记录路径和理由。真正的强权限隔离应由工具、目录沙箱或独立 worktree 实现，不能靠提示词或清单假装完成。

## 3. 机器协议与自然语言分工

以下机器数据使用 JSON：

- `context-manifest.json`；
- `context-packets/<role>.json`。

JSON 由 Python 标准库解析。`allowed_paths` 必须是至少包含一个非空字符串的数组；不使用正则模拟 YAML 隐式类型系统。

需求、方案、AC、开发记录、Review 和测试报告继续使用 Markdown。机器类型约束不得扩散为对角色自然语言表达、推理方式或按需检索的微观限制。

## 4. 委派规则

总控调用 `delegate_task` 时只内联：角色目标、公共最小事实、JSON 上下文包路径、必须读取路径和关键禁止事项。其余材料通过绝对路径引用。子 Agent 不继承当前聊天历史，不能假设已知未明确传递的事实。

上下文包由 `scripts/build_context_packet.py` 生成到任务目录的 `context-packets/<role>.json`。它是读取清单，不是业务内容副本。角色开始读取或执行前，必须以实际工作目录作为进程 cwd 运行 `--check --runtime-root <实际目录>`；脚本会拒绝 cwd 与参数不一致的伪报。`IDENTITY_MISMATCH` 时立即停止，不能用自然语言自述替代机器检查。

## 5. 过期检查

上下文包必须记录：

- `project_root`、`git_toplevel`、`git_common_dir`、`git_dir`；
- `git_head`；
- `current_branch`；
- `worktree_fingerprint`（排除 `.hermes/` 任务资料，覆盖 tracked diff 和非任务目录未跟踪文件元数据）；
- `contract_version`；
- `approved_contract_version`；
- `status_updated_at`；
- `generated_at`。

角色返回必须声明实际使用的上述身份与快照，包括 `consumed_project_root`、`consumed_git_toplevel`、`consumed_git_common_dir`、`consumed_git_dir` 和 `consumed_current_branch`。任何 `must_read` 文件、`context-manifest.json`、批准合同、diff 证据或原始测试证据变化时，主控必须先更新 `status.updated_at`；生成上下文包文件本身不触发更新时间。

Git HEAD、工作区指纹、合同版本、批准合同版本、状态时间或任务阶段不再匹配时，结果标记为 `stale`，不得直接落盘为当前结论；重新生成上下文包并重新委派或局部复核。

Developer 和 Quality 要求 `approved_contract_version` 为正整数且等于 `contract_version`，并且 `verification_preflight: complete`、`delivery_reachability` 为已知枚举。否则不得生成可执行上下文包。预检和风险矩阵按 `references/verification-preflight-and-risk-matrix.md` 执行。

## 6. 角色隔离

- Product 默认不读取源代码全集、开发记录、审查结论和测试报告。
- Architect 默认不读取 Developer 自评、Review 结论和无关模块代码。
- Developer 读取最终批准合同，不读取被替代方案、旧 Review 或其他任务资料。
- Quality 读取原始需求、批准合同、实际 diff、当前代码和原始测试输出；**禁止接收 Developer 主观自评或主控预设结论**。

客观证据包括命令、退出码、原始输出、Git diff、文件内容和可复现步骤。`development.md` 若混有主观评价，不得整体传给 Quality；由总控提取客观证据或提供原始文件/命令输出。

## 7. Token 约束

- 初始公共事实包保持简短，目标约 1,000～2,000 Tokens。
- 初始角色包以路径清单为主，不内联大型文档，目标约 3,000～8,000 Tokens。
- 超长日志只提供失败段和原始文件路径。
- scoped diff 仅覆盖当前任务；无关历史和其他任务默认不传。
- Token 数是软目标，不做会阻止必要上下文读取的死上限。
