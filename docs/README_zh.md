# IC-EconGym 集成电路产业政策与供应链韧性测试平台

15 个产业部门和 1 个政府智能体在共同投入产出约束下运行。平台包含赋能 E1–E5、风险 R1–R5、治理 G1–G5 共 15 项任务，支持任务对照、部门状态回放和匹配种子的策略比较。

## 直接运行（历史 13 部门演示）

以下命令回放旧版轨迹；当前 15 部门实验的输入重建与运行命令见 [15 部门实验版本](IC15_DYNAMIC_VERSION.md)。

```bash
python -m pip install -r requirements_ic.txt
python validate_extension.py
python -m ic_extension.entrypoint --problem_scene ic_g5 --ic_periods 30
python -m scripts_ic.run_all_tasks --out demo_results_v2 --seeds 1,2,3 --arms v1
python -m http.server 8000
```

打开 http://localhost:8000/docs/ 可浏览主页、15 题演示、部门观察和中文论文。静态网页回放已有轨迹；调整政策参数后需重新运行 Python。

## 论文与补充证据

中文稿见 [论文](paper/manuscript_zh.md)，已用 15 部门重跑任务诊断、426 条补充机制轨迹及 [参考文献](paper/references.bib)。方法、结果及 [投稿证据检查](paper/SUBMISSION_EVIDENCE.md) 区分原版与新增实验；R1／G5学习、局部容量外部对照和联合稳健性已完成，详见 [15 部门实验版本](IC15_DYNAMIC_VERSION.md)。诊断复现步骤见 [复现协议](REPRODUCIBILITY.md)。

## 配置和规则

修改 `cfg_ic15/ic_*.yaml` 设置当前任务的冲击、预算和机制参数。查看 `ic_extension/model_v4.py` 中的 `RuleSectorPolicy`、`RuleGovernmentPolicy` 和 `ICEnvironment.step`，以及 `MECHANISMS.md` 的机制索引。`iewm15_v4.py` 提供 `reset / run_agents / step / evaluate` 接口。

本包可以独立运行。若接入原 EconGym，运行 `python install_into_econgym.py <EconGym本地目录>` 前请查看脚本参数。原平台的家庭、银行策略不能直接用于 15 部门动作空间。

## 数据与结论边界

当前动态基准取附件 2020 年 57 部门／15 决策部门矩阵，2018、2023 年表用于结构比较；核验结果见 `reference/io15_summary.json` 和工作区 `outputs/io_15_2018_2020_2023/`。三种进口用途分配为守恒情景，非真实买方观测。15 项任务 P0 共 870 条轨迹，R1／G5 锁定测试 6,000 条，联合稳健性 23,400 条。网页“15 题演示”和旧命令仍回放历史 13 部门版本，当前证据见论文与 `benchmark_results/*_v4/`。动态行为系数为情景值，三个供给通道为合成槽。核实的 460 节点网络有 617 条披露关系及 768 条全来源关系，均为跨年并集，尚无向 15 部门的同年逐产品守恒流量映射。

当前比较包含 R1 部门 IPPO 与 G5 政府 PPO，未调用LLM；独立外部检验仅覆盖容量队列。论文、演示与政策排序均按条件机制实验解释。

[中文论文](paper/manuscript_zh.md) · [数据说明](DATA_CARD.md) · [复现协议](REPRODUCIBILITY.md) · [发布说明](PUBLISHING.md)


项目主页：https://Jinhua188.github.io/IC-EconGym/  
源码：https://github.com/Jinhua188/IC-EconGym  
更新页面：`python -m pip install -r requirements_site.txt` 后执行 `python -m scripts_ic.build_project_site`。修改 `paper/manuscript_zh.md` 后推送 `main`，Pages 自动重建论文与演示。

## 版本、治理与许可

`VERSION=0.3.0` 为待发布版本线；尚未创建对应标签、Release 或 DOI。既有 v0.2.0 发布保留。原创代码及列明的运行文档采用 Apache-2.0；数据、权重和论文许可另见 [LICENSE_SCOPE.md](LICENSE_SCOPE.md) 与 [RIGHTS_REGISTRY.csv](RIGHTS_REGISTRY.csv)。贡献经 Fork／PR，最终合并与发布由 @Jinhua188 决定。参见 [GOVERNANCE.md](GOVERNANCE.md)、[CONTRIBUTING.md](CONTRIBUTING.md) 和 [发布检查](RELEASE_READINESS.json)。
