# 机制与设置索引

## 主体层级

`SectorAgent` 恰有13个，编号与工作区2020年相关部门顺序相同。`GovernmentAgent` 恰有1个。其他42个国内部门、进口来源、最终用户与合成供给通道只参与环境核算或情景供给，不具有独立收益最大化策略。H1—H6作为`sector_roles.yaml`中的产业机制来源标签，不增加主体数。

## 核心函数

| 编号 | 关系 | 代码与设置 | 证据状态 |
|---|---|---|---|
| F1 订单 | (O^d_{rj,t}=a^d_{rj}\hat q_{j,t}+\lambda[I^*_{rj,t}-I_{rj,t}]^+\) | `desired_internal`、`inventory_adjustment` | (a^d)由IO分配情景给出；库存目标是假设 |
| F2 交付 | 国内内部交付在途一期，随后乘边健康与资格；42部门和进口另记 | `pending`、`health`、`qualification` | 基准周期与边状态是假设 |
| F3 生产 | (q_{j,t}=\min\{\hat q_{j,t}+B_{j,t-1},D_{j,t},K^{eff}_{j,t},\min_r M^d_{rj,t}/a^d_{rj},\min_r M^m_{rj,t}/a^m_{rj}\}\) | `input_limit`、`capacity_eff` | 固定价格、固定投入比例的情景生产技术；国产与进口暂不互替 |
| F4 库存与积压 | 按来源扣减投入；未售出入成品库存；未满足订单按`backlog_retention`保留 | `material_domestic`、`material_import`、`finished`、`backlog` | 初始化为零库存加基期在途交付；订单取消率及库存天数待估 |
| F5 价格与收益 | 价格随超额订单变化；收益扣除中间投入、假设劳动其他成本、存货与短缺代价 | `price`、`profit`、`labor_share_of_va` | 加价、成本分解与罚系数未估计 |
| F6 AI转化 | (AI^{eff}=AI\times Absorb\times TimeFit/(1+Friction)\)；作用于有效产能、单位成本和研发效率 | `ai`, `absorption`, `friction`, `time_fit`, `ai_productivity`, `ai_cost_reduction` | AI和吸收能力参数是假设；IO不识别 |
| F7 边压力健康 | 正错配、未满足订单提高压力；协同与修复降低压力；健康随压力下降 | `pressure`, `health`, `repair_credit` | 机制来自前期稿；系数需事件数据估计 |
| F8 供应匹配 | 同一投入部门下三个合成供给通道的Logit选择与容量配给 | `supplier_choice`, `search_precision`, `supplier_channel_capacity` | 通道是情景，不能解释为企业真实边 |
| F9 投资产能 | 企业按基期产出份额投资，政策投资另计；二者经`capacity_lag`期进入可用产能，私人支出计入现金流 | `capacity_projects`, `capital_efficiency` | 融资可得性、投资效率与滞后未估计 |
| F10 技术研发 | 技术状态受研发支出、AI效率增益与折旧影响 | `tech`, `rd_efficiency`, `innovation_ai_gain`, `tech_depreciation` | 需研发与创新指标校准 |
| F11 协同 | 审计及契约激励进入Logit协同概率；高协同后用KKT分配五类努力 | `_nash_reward_fraction`, `_resource_allocation` | 条件Nash是可运行的风格化合同，并非前期论文参数的无损移植 |
| F12 政府 | 六类支出总和不得超过实验预算；福利权重在YAML中设置 | `GovernmentAction`, `budget_share`, `policy`, `welfare_weights` | 权重是研究者设定，不能由IO推出 |

`qualification`提高既有部门边的可用比例，`inventory`从模型外的42部门边界购买额外投入库存，`edge_repair`在当期压力更新后生效。`equipment_availability`、`manufacturing_yield`、`packaging_limit`分别限制部门8产能，默认值均为1。`wip`记录平滑的制造活动状态，目前不构成独立的逐工序排程模型。设计适配、材料批次一致性、具体晶圆良率及先进封装不是13部门表中的独立观测流；这些角色标签在`sector_roles.yaml`中保留，若要估计细节须另接企业或工艺数据。

## 直接可改的任务字段

| YAML字段 | 含义 |
|---|---|
| `modules` | 启用的状态转移机制；可选`edge`, `ai`, `forecast`, `supplier_choice`, `price`, `market_power`, `investment`, `innovation`, `coordination`, `contract`, `qualification`, `inventory`, `equipment`, `manufacturing`, `packaging` |
| `import_case` | 三种进口用途分配假设之一 |
| `periods`, `seed` | 仿真季度数和随机种子 |
| `demand_sector`, `demand_growth`, `demand_shock` | 最终需求增长及短期冲击 |
| `shock` | 指定部门、起止期、产能损失和外部投入损失 |
| `budget_share`, `policy.channels`, `policy.sector_weights`, `policy.start_period` | 总财政预算占13部门单季基期产出之比、六类支出份额、目标部门权重和首次支出期 |
| `absorption`, `friction`, `time_fit` | AI有效转化假设；不填时采用13角色表默认值 |
| `forecast_error_sd`, `common_forecast_share`, `ai_forecast_gain` | 预测误差与共同误判假设 |
| `search_precision`, `supplier_channel_capacity`, `hhi_markup` | 同类通道选择、拥堵及市场势力情景 |
| `capacity_lag`, `capital_efficiency`, `rd_efficiency` | 投产与研发动态假设 |
| `contract` | 平台质量、审计、处罚和Nash议价权重 |
| `variants` | 与主情景共用随机种子的对照设置；`channels`整体替换，其他字典逐项覆盖 |

输入金额和结果金额均为固定2020年价格的万元／季度。`budget_share`乘以13部门基期单季产出总和形成**整个实验的一次性总预算**。若需要分期预算，应调整政府策略，而非反复将总预算加到每一期。

## 未识别事项与扩展接口

现有IO表识别的是部门核算结构，不识别企业真实边、企业策略、认证时滞、维修周期、AI吸收系数或财政福利权重。原EconGym的PPO、SAC、LLM和行为克隆类是为其家庭、市场、银行等角色编写；新环境仅实现相同的观察—行动—奖励范式与`main.py`场景入口。要比较这些算法，应另写适配器，将13个部门观察编码为固定张量、将算法输出解码为`SectorAction`及`GovernmentAction`，并使用本环境的同一状态转移函数。不得把原仓库现成`firm_alg`直接指定给13部门后声称完成算法比较。

企业层扩展的接口是：用同年企业产品收入估计部门内覆盖率，分配企业基期产出和采购预算；已披露客户关系是商业锚点，候选边仍为支持集；真实物理流必须与部门总量、进口及样本外节点共同守恒。当前包刻意不把8,364条候选边直接载入13部门经济环境。
