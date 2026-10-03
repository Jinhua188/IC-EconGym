# IEWM 附件代码的 13 部门适配与基准实验

## 适配范围

附件《产业经济世界模型 IEWM 系统蓝图 企业数据与可执行代码完整版》附录 F 的 `industrial_world_model` 是以 206 家企业、H1—H6 角色、候选企业边和合成投入配方运行的企业级模型。当前扩展包是 13 个产业部门加 1 个政府智能体，2020 年 55 部门投入产出表为核算锚点，其他 42 个部门、进口与最终使用分开记账。两种粒度不能通过把 `Firm` 改名为 `SectorAgent` 合并。附件自身还报告默认 `top_k=3` 时无冲击服务率仅 0.0962，尚未完成无冲击稳态校准。

已适配附件的 `reset → run_agents → step → evaluate` 运行接口，见 `ic_extension/iewm13.py`。`step` 始终调用原有 `ICEnvironment.step`，不改变 15 题的生产和核算机制；因此新基准不会把候选边当成真实部门货流。部门策略为原规则、需求跟随、带库存目标的平滑决策；政府策略为均匀、后向关联度、关联度与短缺共同靶向。每组策略收到同样的观察字段和行动类型。政府三策略使用相同六类支出渠道、起始期及总预算。

发布前的来源审计核对附件与企业数据哈希、206 个企业节点、8,364 条候选边及企业到部门映射。审计结果保存在 `reference/iewm13_source_audit.json`。企业映射模板没有已识别业务份额，候选边没有逐产品交易金额，因此企业数据**没有**被分配到 13 部门的基期货流。H3 设计、H4 制造、H5 封测也不能直接当作部门 8 的三个独立投入产出节点。

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

运行性能脚本在同一机器上对 15 题各测 3 次、每次 30 期，输出 `runtime_runs.csv`、`runtime_summary.csv` 与机器环境记录。它测量固定 13 部门环境的采样成本；进程 RSS 不是单个环境的净增内存，运行结果不能外推到 206 个企业智能体。

## 外部数据对照的接入条件

`scripts_ic/compare_external_baseline.py` 提供严格的 2020 年部门基期对照入口。输入需要 13 行，字段为 `sector_id,observed_annual_output_wanyuan,source_name,source_year,measurement_scope`，且外部数据须独立于现有投入产出工作簿、部门范围与计价口径可比。例如：

```powershell
python -m scripts_ic.compare_external_baseline --observed path/to/independent_2020_sector_output.csv --out benchmark_results/external_2020
```

目前工作区未核实到满足这些条件的 13 部门独立观察表，因此**没有生成外部验证结果**。已有 206 家企业的最新年指标是 2024 年且为 H 角色口径，不能直接充当 2020 年 13 部门实际产出。取得可比来源后，还须人工核查统计范围和价格口径；脚本只能检查字段及年份。

## 论文使用边界

现有结果可以支持“投入产出约束的 13 部门环境、可复现策略比较与参数稳健性框架”。顶会级基准主张仍需补充至少一种真正训练过的部门／政府策略、独立外部验证、跨任务训练测试划分和公开可复现实验协议。不得把当前启发式策略比较写成 PPO、LLM 或行为克隆基准；不得把企业候选边写成已观测交易网络。


版本 0.2.0 增加外生最终需求履约指标。代码中的总短缺仍含策略生成的内部订单；两组基准已重跑，详见中文论文及 `paper/results_summary.json`。来源审计摘要保留于 `reference/`，原始企业数据和内部附件不随仓库发布。
