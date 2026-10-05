# v0.3.0 治理整合与发布准备

## 版本含义

本次将 `VERSION` 更新为 `0.3.0`，用于待发布版本线。CHANGELOG 保留 Unreleased 标记；v0.3.0 标签、Release 和 DOI 尚未创建。既有 v0.2.0 发布保持原指向。

## 已整合内容

治理包与现有研究平台合并，包括代码许可及适用范围、NOTICE、作者元数据、贡献规则、最终决策权、路线图、安全政策、CODEOWNERS、四类 Issue 表单、PR 模板、Release Notes 和 Zenodo 指南。README 保留原版及学习版入口、核算边界和复现命令。论文与实验结果未改写。

软件作者由仓库所有者提供：Jinhua Gu，Guangdong University of Technology，ORCID 0009-0002-2310-6150。CITATION.cff 记录姓名及 ORCID，单位记录在 AUTHOR_METADATA.md。

## 检查的范围

- `validate_extension.py`：原环境核算、任务、最终需求和预算检查。
- `scripts_ic.verify_upgrade`：独立训练记录与检查点身份、训练／验证／测试隔离、学习适配器、行动边界及容量队列；不重新训练。
- `scripts_ic.check_governance`：CFF 1.2.0 官方 schema、版本一致性、Issue／工作流结构、研究快照哈希和公共文件清单。schema 从固定上游提交读取并校验 SHA-256；离线可传入 `--schema-file`。
- `scripts_ic.check_governance --publication`：在上述工程检查后核查人工确认记录。待确认项使其退出码为 2；工程错误退出码为 1。

`RESEARCH_SNAPSHOT.sha256` 固定本次整合前提交 bdb04be 的 185 个研究源文件与产物，包括环境、任务、学习实现、检查点、划分、数据和论文。`MANIFEST.sha256` 覆盖本次公共工作树。前者用于发现研究内容被意外改动，后者用于核对当前分发内容；两者不判断科学真实性或版权。

## 结果的解释

保留 R1 IPPO 在奖励提高时交付下降、G5 PPO 改善区间跨零、局部容量队列未超过线性趋势，以及原配置下的非激活机制。联合参数实验为探索性情景比较。独立外部案例只检查物理容量组件，并使用已知历史资本投入作条件回放；不验证全国 13 部门动态模型。

## 仍待确认

1. 权利：RIGHTS_REGISTRY.csv 中 pending 类别须逐类核查再分发权利，或从正式归档提交移除。代码采用 Apache-2.0 不自动授权处理数据、权重或论文。
2. Zenodo：所有者已回复尚未连接。本次不执行账户连接，不声称已取得 DOI。
3. 发布：确认权利和归档条件后，由 @Jinhua188 决定实际发布日期及发布，才填写 date-released、通过 publication 检查并创建新标签。

GitHub 远程规则的实际状态见 GITHUB_SETTINGS_CHECKLIST.md 及仓库 Settings。只提交规则配置文件不会自动启用保护。

## 本次核查记录

2026-10-05 本地执行：15 题环境检查通过；20 个训练实例的检查点及代码哈希匹配，8,000 个训练情景记录与验证／测试种子隔离，R1/G5 学习适配器各 30 期与参考运行一致，容量队列累加及到期检查通过。治理检查核对 185 个研究文件，并验证 CFF、表单和当前公共文件清单。

网页构建现默认复用既有图表，避免在治理更新中改写 SVG 时间戳与内部标识；重画图表须显式使用 `python -m scripts_ic.build_project_site --refresh-figures` 并更新研究产物版本与哈希。

main 和两项标签规则已通过 GitHub API 启用并读回；私密漏洞报告已启用。正常合并仍须通过 PR 与两个 Actions 检查。本次未创建 v0.3.0 标签或 Release。
