# 15 项条件机制任务

任务配置是可执行定义。以下字段来自发布版本 YAML，不代表经验估计。比较最终需求履约时应共享外生需求，并同时报告财政成本与私人投入。

## E1 AI有效生产率

AI吸收能力如何改变同等采用投入的产出回报？

机制依据：AI采用必须经吸收能力、时间可行性和组织摩擦转化为有效AI能力。

启用机制：edge, ai

对照臂：baseline_low_ai, high_ai_low_absorption, high_ai_high_absorption

配置文件：[ic_e1.yaml](cfg_ic/ic_e1.yaml)

共同评估：最终需求履约与短缺、产出、增加值、机制状态、总订单短缺、政府实际支出。随机性是否生效须检查该题配置。

## E2 AI预测与供应链协同

降低个体预测误差是否同时降低库存和短缺？

机制依据：AI降低特异性预测误差，但共同模型可能引入相关误差。

启用机制：edge, forecast, ai

对照臂：conventional_forecast, ai_independent_forecast, ai_shared_model_forecast

配置文件：[ic_e2.yaml](cfg_ic/ic_e2.yaml)

共同评估：最终需求履约与短缺、产出、增加值、机制状态、总订单短缺、政府实际支出。随机性是否生效须检查该题配置。

## E3 AI与研发效率

AI与研发共同投入能否加快技术状态积累？

机制依据：知识生产函数中AI与R&D互补，并通过投入产出邻接产生知识溢出。

启用机制：edge, innovation, ai

对照臂：rd_without_ai_complement, moderate_ai_rd_complement, strong_ai_rd_complement

配置文件：[ic_e3.yaml](cfg_ic/ic_e3.yaml)

共同评估：最终需求履约与短缺、产出、增加值、机制状态、总订单短缺、政府实际支出。随机性是否生效须检查该题配置。

## E4 AI与供应商匹配

较高搜索精度如何改变同类供给通道的拥堵？

机制依据：信息改善使稀缺中间投入更倾向于流向系统关键且AI可识别的用途。

启用机制：edge, supplier_choice

对照臂：proportional_allocation, moderate_ai_allocation, strong_ai_allocation

配置文件：[ic_e4.yaml](cfg_ic/ic_e4.yaml)

共同评估：最终需求履约与短缺、产出、增加值、机制状态、总订单短缺、政府实际支出。随机性是否生效须检查该题配置。

## E5 AI需求与产业结构

下游需求增长如何经部门网络传导至产出与扩产？

机制依据：最终需求冲击通过直接与间接投入需求、价格和投资时滞改变产业结构。

启用机制：edge, price, investment

对照臂：no_ai_demand_shock, moderate_ai_demand, high_ai_demand

配置文件：[ic_e5.yaml](cfg_ic/ic_e5.yaml)

共同评估：最终需求履约与短缺、产出、增加值、机制状态、总订单短缺、政府实际支出。随机性是否生效须检查该题配置。

## G1 AI补贴配置

固定预算下按何种部门权重配置AI支持更有效？

机制依据：同一财政预算下，不同靶向规则产生不同的边际社会收益。

启用机制：edge, ai

对照臂：uniform, output_scale, ai_gap, backward_linkage, linkage_stress_proxy

配置文件：[ic_g1.yaml](cfg_ic/ic_g1.yaml)

共同评估：最终需求履约与短缺、产出、增加值、机制状态、总订单短缺、政府实际支出。随机性是否生效须检查该题配置。

## G2 AI与实体能力组合政策

AI与产能、研发及认证补贴的组合能否缓解瓶颈？

机制依据：数字能力与物理承接能力具有互补性，单一AI政策可能受实体瓶颈约束。

启用机制：edge, ai, investment, innovation, qualification

对照臂：ai_only, physical_only, coordinated_mix

配置文件：[ic_g2.yaml](cfg_ic/ic_g2.yaml)

共同评估：最终需求履约与短缺、产出、增加值、机制状态、总订单短缺、政府实际支出。随机性是否生效须检查该题配置。

## G3 数字契约与可核验协同

平台核验与契约激励如何改变协同采用及资源配置？

机制依据：核验性提高有效激励，再经Logit影响高协同概率，并由KKT在产能预留、库存、反馈、联合验证和恢复之间配置有限资源。

启用机制：edge, coordination, contract, qualification

对照臂：low_verifiability, medium_verifiability, high_verifiability

配置文件：[ic_g3.yaml](cfg_ic/ic_g3.yaml)

共同评估：最终需求履约与短缺、产出、增加值、机制状态、总订单短缺、政府实际支出。随机性是否生效须检查该题配置。

## G4 库存认证与修复

同预算下库存、资格和边修复对供给冲击有何差异？

机制依据：韧性行动的缓释收益必须超过搜索、认证、协调和资源重配摩擦。

启用机制：edge, qualification, inventory

对照臂：inventory_buffer_bias, joint_verification_bias, recovery_bias, balanced_adaptive

配置文件：[ic_g4.yaml](cfg_ic/ic_g4.yaml)

共同评估：最终需求履约与短缺、产出、增加值、机制状态、总订单短缺、政府实际支出。随机性是否生效须检查该题配置。

## G5 多目标政策组合

组合治理是否优于同预算的单项政策？

机制依据：单项最优政策的简单叠加未必系统最优，多工具政策需要共同考虑产出、技术、韧性、价格和财政成本。

启用机制：edge, ai, investment, innovation, qualification, inventory, coordination

对照臂：ai_department_only, industry_department_only, science_department_only, fixed_uncoordinated_mix, structured_adaptive_mix

配置文件：[ic_g5.yaml](cfg_ic/ic_g5.yaml)

共同评估：最终需求履约与短缺、产出、增加值、机制状态、总订单短缺、政府实际支出。随机性是否生效须检查该题配置。

## R1 需求扩张与产能周期

扩产时滞如何改变需求冲击后的短缺和价格路径？

机制依据：蛛网式供需调整与不可逆/滞后投资导致动态过度反应。

启用机制：edge, price, investment

对照臂：short_capacity_lag, benchmark_lag, long_capacity_lag

配置文件：[ic_r1.yaml](cfg_ic/ic_r1.yaml)

共同评估：最终需求履约与短缺、产出、增加值、机制状态、总订单短缺、政府实际支出。随机性是否生效须检查该题配置。

## R2 AI扩散与承接错配

AI变化负荷超过下游吸收能力时会否提高边压力？

机制依据：AI扩散本身不是风险，AI诱发调整负荷超过界面吸收能力时才形成正错配。

启用机制：edge, ai

对照臂：balanced_ai_absorption, front_end_ai_low_absorption, mismatch_with_coordination

配置文件：[ic_r2.yaml](cfg_ic/ic_r2.yaml)

共同评估：最终需求履约与短缺、产出、增加值、机制状态、总订单短缺、政府实际支出。随机性是否生效须检查该题配置。

## R3 共同预测误判

相关预测误差是否放大订单与短缺波动？

机制依据：个体预测误差下降与跨主体误差相关性上升之间存在系统层权衡。

启用机制：edge, forecast

对照臂：diversified_models, moderate_common_model, highly_homogeneous_models

配置文件：[ic_r3.yaml](cfg_ic/ic_r3.yaml)

共同评估：最终需求履约与短缺、产出、增加值、机制状态、总订单短缺、政府实际支出。随机性是否生效须检查该题配置。

## R4 算法采购与供给集中

提高搜索精度会否使同类供应通道拥堵？

机制依据：个体最优匹配可能通过算法羊群效应提高供应来源集中和系统脆弱性。

启用机制：edge, supplier_choice, price

对照臂：heterogeneous_procurement, moderate_ai_herding, strong_ai_herding

配置文件：[ic_r4.yaml](cfg_ic/ic_r4.yaml)

共同评估：最终需求履约与短缺、产出、增加值、机制状态、总订单短缺、政府实际支出。随机性是否生效须检查该题配置。

## R5 AI异质性与市场势力

效率差异和采购集中如何共同影响加价与产出？

机制依据：AI导致的成本异质性通过利润、投资和价格反馈改变产出与价值集中度。

启用机制：edge, supplier_choice, price, market_power, ai

对照臂：balanced_ai, core_sector_ai_advantage, core_advantage_high_markup

配置文件：[ic_r5.yaml](cfg_ic/ic_r5.yaml)

共同评估：最终需求履约与短缺、产出、增加值、机制状态、总订单短缺、政府实际支出。随机性是否生效须检查该题配置。
