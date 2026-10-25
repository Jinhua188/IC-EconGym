# IEWM 附件代码的 13 部门适配与基准实验

## 适配范围

本适配包以 13 个产业部门和 1 个政府智能体运行，2020 年 55 部门处理后投入产出表为核算锚点；其他 42 个部门、进口与最终使用分开记账。企业关系网络单独分析，不改变部门主体和基期货流。

已适配附件的 `reset → run_agents → step → evaluate` 运行接口，见 `ic_extension/iewm13.py`。`step` 始终调用原有 `ICEnvironment.step`，不改变 15 题的生产和核算机制；因此新基准不会把企业披露关系当成真实部门货流。部门策略为原规则、需求跟随、带库存目标的平滑决策；政府策略为均匀、后向关联度、关联度与短缺共同靶向。每组策略收到同样的观察字段和行动类型。政府三策略使用相同六类支出渠道、起始期及总预算。

企业网络采用核实后的 460 节点版本：617 条披露交易关系、768 条全来源关系，均为跨公告年并集。核验结果见工作区 `outputs/network_460_analysis/results/validation.json`；公共仓库仅保留聚合摘要 `reference/network_460_summary.json`。这些关系尚未取得可守恒映射到 2020 年 13 部门的逐产品业务份额，故没有进入基期货流。

## 运行策略比较与敏感性

在本扩展包根目录执行：

```powershell
python -m scripts_ic.run_strategy_benchmark --task ic_r1 --dimension sector --ofat --out benchmark_results/r1_v2
python -m scripts_ic.run_strategy_benchmark --task ic_g5 --dimension government --ofat --out benchmark_results/g5_v2
python -m scripts_ic.benchmark_runtime --out benchmark_results/runtime_v2
```

每个任务使用 10 个种子、30 期、3 个进口分配情景及 5 个参数的 ±20% 单因素扰动，共 13 种结构／参数情景、390 次运行。相同种子及情景下，各策略共享同一冲击强度。种子改变的冲击乘数服从**设定**的相对标准差 0.04，不能据此计算经验参数的不确定区间。政府比较将 `spend_fraction` 统一设为 0.25，使靶向规则能够在后续期利用新观察；这一设置不同于原任务 YAML 的一次性支出，应在论文方法节明示。

输出文件：

| 文件 | 内容 |
|---|---|
| `run_metrics.csv` | 每种子、情景、策略的累计产出／短缺／福利、财政和私人支出及期末状态 |
| `paired_differences.csv` | 同种子、同情景下相对基线的逐次差异 |
| `paired_summary.csv` | 差异均值和种子范围 |
| `metadata.json` | 参数扰动、冲击随机化、策略及证据等级 |

R1 基准情景下，规则策略的 30 期累计短缺低于需求跟随和平滑策略。G5 基准情景下，三种政府靶向策略财政支出相等；短缺和福利差异很小。具体数值与 13 个情景中的排序见 CSV。以上均属于给定模型和情景参数下的比较，不是现实政策估计，也不是 RL 或 LLM 性能比较。当前 `co-evolve`、实时 `align`、企业网络重连及学习策略尚未接入 13 部门运行时。

运行性能脚本在同一机器上对 15 题各测 3 次、每次 30 期，输出 `runtime_runs.csv`、`runtime_summary.csv` 与机器环境记录。它测量固定 13 部门环境的采样成本；进程 RSS 不是单个环境的净增内存，运行结果不能外推到 460 个企业智能体。

## 外部数据对照的接入条件

`scripts_ic/compare_external_baseline.py` 提供严格的 2020 年部门基期对照入口。输入需要 13 行，字段为 `sector_id,observed_annual_output_wanyuan,source_name,source_year,measurement_scope`，且外部数据须独立于现有投入产出工作簿、部门范围与计价口径可比。例如：

```powershell
python -m scripts_ic.compare_external_baseline --observed path/to/independent_2020_sector_output.csv --out benchmark_results/external_2020
```

目前工作区未核实到满足这些条件的 13 部门独立观察表，因此**没有生成外部验证结果**。460 节点关系矩阵是跨公告年并集，不能直接充当 2020 年 13 部门实际产出。取得可比来源后，还须人工核查统计范围和价格口径；脚本只能检查字段及年份。

## 论文使用边界

现有结果可以支持“投入产出约束的 13 部门环境、可复现策略比较与参数稳健性框架”。顶会级基准主张仍需补充至少一种真正训练过的部门／政府策略、独立外部验证、跨任务训练测试划分和公开可复现实验协议。不得把当前启发式策略比较写成 PPO、LLM 或行为克隆基准；不得把跨年披露关系写成同年、完整且具有已知投入权重的交易网络。


版本 0.2.0 增加外生最终需求履约指标。代码中的总短缺仍含策略生成的内部订单；两组基准已重跑，详见中文论文及 `paper/results_summary.json`。460 节点网络的聚合核验摘要保留于 `reference/`，原始企业数据和内部附件不随仓库发布。
