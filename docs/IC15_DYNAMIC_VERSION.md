# IC-EconGym 15 部门动态版本

本版本使用附件 2020 年“完表”的 57 部门竞争型投入产出矩阵，其中前 15 个部门为决策主体，后 42 个部门为外部国内边界。2018 和 2023 年矩阵可由 `io_year` 读取，用于结构核对；正式动态基准年为 2020 年。金额按表内现价万元读取，模型沿用年度除以四的季度基准设定，未估计季节性或跨年价格指数。

三张表只观测部门进口总量，不观测进口最终去向。`scripts_ic/io15/build_dynamic_inputs.py` 对每年构造“按可分配用途比例”“中间使用优先”“国内最终使用优先”三种情景。出口不分配进口；负存货变动视为库存提取，不参与进口分配。每个情景逐行检查竞争型使用、进口、国内产出及投入列平衡。三种分配均为识别不足下的机制假设。

`ic_extension/model_v4.py` 实现 15 部门与政府动态环境；`cfg_ic15/` 保留 15 项任务并将旧任务的部门索引映射到新表。新部门 9 采用制造与封测角色，新部门 15 采用应用角色；这是基于表内分组的建模指定，不代表观测到独立企业或工艺产线。`calibration/ai_proxy_initialization_15.json` 将原功能代理扩展至新增部门，未提供新增行业的独立测量。行为系数及 AI 转化仍属情景参数。

从包含本仓库和 `outputs/io_15_2018_2020_2023/` 的工作区运行：

```powershell
cd IC-EconGym
python -m scripts_ic.io15.build_io15
python -m scripts_ic.io15.build_dynamic_inputs
python -m scripts_ic.io15.validate_io15
python -m scripts_ic.run_upgrade_experiments_v4 --package p0
python -m scripts_ic.run_strategy_benchmark_v4 --task ic_r1 --dimension sector --ofat --out benchmark_results/r1_v4
python -m scripts_ic.run_strategy_benchmark_v4 --task ic_g5 --dimension government --ofat --out benchmark_results/g5_v4
python -m scripts_ic.run_manuscript_diagnostics_v4
python -m scripts_ic.run_threshold_diagnostics_v4
python -m scripts_ic.benchmark_runtime_v4
python -m scripts_ic.run_learning_upgrade_v4 --workers 4 --steps 12000
python -m scripts_ic.verify_upgrade_v4
python -m scripts_ic.run_upgrade_experiments_v4 --package p1 --workers 4
python -m scripts_ic.run_upgrade_experiments_v4 --package p3 --workers 4
python -m scripts_ic.run_upgrade_experiments_v4 --package p4 --workers 4
python -m scripts_ic.summarize_upgrade_v4
python -m scripts_ic.validate_ic15_results
```

若投入产出派生文件不在默认工作区位置，配置 `io15_dir` 指向包含 `io_use_15_2020_*.npz` 的目录。项目隔离环境 `.venv-ic15` 用于兼容本机 PyTorch 2.3.0 与 NumPy 1.26.4。模型和结果是机制仿真，不构成现实政策效果识别。来源工作簿及派生逐部门矩阵的公开再分发仍受项目权利登记约束。

逐期日志中的 `engine_version=v0.3-experimental` 沿用核心状态转移规则的历史标识；以各 v4 实验目录元数据中的 `engine_version=v0.4-ic15-experimental`、来源哈希及 15 部门输入作为本次结果版本依据。
