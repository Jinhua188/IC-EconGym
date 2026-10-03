# IC-EconGym 集成电路产业政策与供应链韧性测试平台

13 个产业部门和 1 个政府智能体在共同投入产出约束下运行。平台包含赋能 E1–E5、风险 R1–R5、治理 G1–G5 共 15 项任务，支持任务对照、部门状态回放和匹配种子的策略比较。

## 直接运行

```bash
python -m pip install -r requirements_ic.txt
python validate_extension.py
python -m ic_extension.entrypoint --problem_scene ic_g5 --ic_periods 30
python -m scripts_ic.run_all_tasks --out demo_results_v2 --seeds 1,2,3 --arms v1
python -m http.server 8000
```

打开 http://localhost:8000/docs/ 可浏览主页、15 题演示、部门观察和中文论文。静态网页回放已有轨迹；调整政策参数后需重新运行 Python。

## 论文与补充证据

中文稿见 [论文](paper/manuscript_zh.md)，已补充 426 条机制诊断及 [参考文献](paper/references.bib)。方法、结果及 [投稿证据检查](paper/SUBMISSION_EVIDENCE.md) 区分原版与新增实验；R1／G5学习、局部容量外部对照和联合稳健性已完成，详见 [实验升级](EXPERIMENT_UPGRADE.md)。诊断复现步骤见 [复现协议](REPRODUCIBILITY.md)。

## 配置和规则

修改 `cfg_ic/ic_*.yaml` 设置冲击、预算和机制参数。查看 `ic_extension/model.py` 中的 `RuleSectorPolicy`、`RuleGovernmentPolicy` 和 `ICEnvironment.step`，以及 `MECHANISMS.md` 的机制索引。`iewm13.py` 提供 `reset / run_agents / step / evaluate` 接口。

本包可以独立运行。若接入原 EconGym，运行 `python install_into_econgym.py <EconGym本地目录>` 前请查看脚本参数。原平台的家庭、银行策略不能直接用于 13 部门动作空间。

## 数据与结论边界

投入产出表提供核算结构；55 部门细分来自收入比例分劈，三种进口使用分配为假设。动态行为系数为情景值，三个供给通道为合成槽。206 企业候选关系尚未进行守恒的投入流量分配。

新增比较包含R1部门IPPO与G5政府PPO，未调用LLM；独立外部检验仅覆盖容量队列。论文、演示与政策排序均按条件机制实验解释。

[中文论文](paper/manuscript_zh.md) · [数据说明](DATA_CARD.md) · [复现协议](REPRODUCIBILITY.md) · [发布说明](PUBLISHING.md)


项目主页：https://Jinhua188.github.io/IC-EconGym/  
源码：https://github.com/Jinhua188/IC-EconGym  
更新页面：`python -m pip install -r requirements_site.txt` 后执行 `python -m scripts_ic.build_project_site`。修改 `paper/manuscript_zh.md` 后推送 `main`，Pages 自动重建论文与演示。
