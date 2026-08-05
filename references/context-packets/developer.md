# Developer 上下文包

## Must Read

- 当前批准版本的 `plan.md`、`acceptance.md`、`test-plan.md` 和 `verification-preflight.md`
- `request.md`（仅用于追踪原始意图）
- 项目规则、默认/保护路径和当前 Git 状态
- 相关代码、测试及已验证命令
- 以实际工作目录作为进程 cwd 执行 packet 的 `--check --runtime-root` 并获得 `FRESH`；参数与 cwd 不一致会被拒绝

## May Read

- 与当前 AC 直接相关的接口、数据模型、调用方和文档；
- 为处理真实编译/测试错误所需的依赖代码；
- 超出默认读取范围但完成任务确实需要的文件，返回时记录路径和原因。

## Must Not Read

- 被批准合同取代的旧方案和已关闭待决项；
- 旧 `review.md`、其他任务目录、无关模块；
- 密钥与 `.env` 内容。

生成包前必须满足 `approved_contract_version == contract_version > 0` 且验证预检已完成。Developer 按合同驱动风险测试矩阵执行测试优先的实现。`allowed_paths` 是默认读取与审计范围，不是权限沙箱或绝对写入边界；实际修改范围仍由批准方案、项目规则和禁改范围共同决定，Developer 不得自行改变合同。
