# 公共最小事实包

所有角色共享，但只包含事实和路径，不复制大段正文。机器包使用 JSON。

## 必需字段

- 任务：ID、类型、等级、阶段和状态。
- 项目：规范化 `project_root`、`git_toplevel`、`git_common_dir`、当前 worktree 的 `git_dir`、当前分支、Git HEAD、工作区指纹和脏文件摘要。
- 合同：`contract_version`、`approved_contract_version`、`status_updated_at`。
- 范围：默认读取路径、保护路径、项目规则路径。
- 环境：已验证构建/测试命令、`verification_preflight`、`delivery_reachability` 与限制。
- 安全：禁止推送、合并、部署、生产操作和密钥读取等动作。

`allowed_paths` 是默认读取与审计范围，不是操作系统权限沙箱。May Read 可以基于任务需要扩展，但必须记录新增路径和原因。实际强权限边界由工具、项目规则、禁改范围或隔离 worktree 实现。每个角色在读取或执行前必须以实际目录作为进程 cwd 通过 `--check --runtime-root`；参数与 cwd 不一致或错误 worktree 均不得继续。

## 不得包含

- 完整聊天记录；
- 完整项目文档或全仓库源码；
- 其他任务目录；
- 任一角色的主观结论；
- 密钥、令牌、`.env` 内容。
