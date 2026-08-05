# Quality 上下文包

## Must Read

- 原始 `request.md`
- 当前批准版本的 `plan.md`、`acceptance.md`、`test-plan.md` 和 `verification-preflight.md`
- 实际 scoped Git diff、变更后代码
- 原始测试命令、退出码、输出和环境限制
- 项目规则与公共最小事实包
- 以实际工作目录作为进程 cwd 执行 packet 的 `--check --runtime-root` 并获得 `FRESH`；参数与 cwd 不一致会被拒绝

## May Read

- 受影响调用方、回归测试、接口/数据/权限实现；
- 为复现问题所需的局部日志和配置（不含密钥）。

## Must Not Read

- Developer 的完成声明、自评分、风险判断或推荐 PASS；
- 主控预设结论；
- 与当前 diff 无关的全仓库代码、其他任务 Review 和旧发布总结。

生成包前必须满足 `approved_contract_version == contract_version > 0` 且验证预检已完成。Quality 只能依据客观证据逐条核验 AC、风险测试矩阵和未验证 Gate，并输出 PASS/FAIL/BLOCKED 与分级问题。
