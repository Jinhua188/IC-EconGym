# v0.3 实验与复现

原 `model.py`、原配置和历史结果继续保留。新增 `model_v3.py` 支持机制诊断、可设置 AI 初值和资格初值，以及三种配给规则。向量化计算在原 15 题默认规则路径上与旧引擎一致；局部容量队列函数与外部制造案例共用。

## 环境

在独立 Python 3.12 环境安装 `requirements_learning.txt`。实测 CPU PyTorch 2.3.0 与 NumPy 1.26.4；不改动用户其他 Python 项目。

```powershell
python -m scripts_ic.run_upgrade_experiments --package p0
python -m scripts_ic.run_learning_upgrade --workers 6 --steps 12000
python -m scripts_ic.run_upgrade_experiments --package p1 --workers 6
python -m scripts_ic.fetch_external_smic
python -m scripts_ic.run_external_capacity
python -m scripts_ic.run_upgrade_experiments --package p3 --workers 6
python -m scripts_ic.run_upgrade_experiments --package p4 --workers 6
python -m scripts_ic.run_threshold_diagnostics
python -m scripts_ic.summarize_upgrade
python -m scripts_ic.verify_upgrade
```

附件预处理可选命令为 python -m scripts_ic.prepare_upgrade_data 和 python -m scripts_ic.build_parameter_registry；默认从已有处理表运行。原始附件不是公共仓库自带资料；已公开的处理矩阵、代理和来源表可重现实验。重新执行附件处理需要原始工作簿和论文。企业原始公告按官方链接下载到忽略目录 `external_validation/raw/`，公共包保留来源链接、哈希、页码和提取数值。

P0 覆盖所有 15 题和配置中全部命名臂，包含与历史臂同义的配置名，不能视为同等数量的独立经济机制。压缩逐期日志保存行动、奖励、到货、队列、预算及绑定上界。P1 训练 R1 部门 IPPO 与 G5 政府 PPO，每种 10 个独立训练实例、12,000 环境步；每实例另使用固定验证情景选择检查点。每个环境步包含该期全部部门及政府行动，不能乘 13 计作额外环境样本。

测试集在训练前写入 `benchmark_splits/locked_scenarios_v3.json`。每任务包含 100 个同分布与 100 个未见结构／冲击情景；模型按训练实例分别评价。G5 将混合年份的 AI 代理映射作为条件初值，R1 保留无 AI 的原机制。合法随机和单期近似优化是独立实现的基线；单期优化只求解定义的局部代理目标，不是全经济最优控制。

P3 主实验为 18,000 条轨迹；额外两种配给规则在预先选定的前 30 个参数样本上产生 5,400 条轨迹。探索区间不具有经验概率含义。学习策略使用预定训练种子 101—105，与五个情景种子对应，报告这一训练变异来源。

P4 在其他实验结束后计时。并行数代表独立环境批量数，始终保持每环境 13 个部门和 1 个政府，不声称智能体数量扩展性。

## 已知边界

学习策略训练不等于真实企业行为估计；有限训练预算不保证收敛或求得均衡。价格、投资、AI、库存、合同等全国模型动态系数仍为情景值。容量案例为使用已知历史资本投入的局部物理单位回放，不能直接替换全国价值量投资系数，也不能验证整个 13 部门环境。

## 调用检查点或接入EconGym

从仓库根目录运行：

```powershell
python -m ic_extension.entrypoint_v3 --problem_scene ic_r1 --split test_id --scenario 0 --sector-policy learned
python -m ic_extension.entrypoint_v3 --problem_scene ic_g5 --split test_ood --scenario 0 --government-policy learned
python install_into_econgym.py <本地EconGym目录> --include-upgrade
```

最后一条会将学习模块、检查点、代理及锁定划分加入指定的本地EconGym工作副本。安装学习依赖使用requirements_learning.lock.txt的独立环境。原main.py的IC分发入口仍执行原版引擎；v0.3使用entrypoint_v3或World13V3明确调用。本轮未在原仓库家庭／银行策略上训练，也未验证其策略可直接复用。


追加阈值诊断18条，单独版本和配置记录；它不替代600条扫描中未触发的R2结果。性能批量每种重复3次，最多6进程，包含环境构造和规则运行。外部原始公告需先下载才可重跑提取；首次下载受官方站点访问状态影响，已提取CSV可检查报告值。

## 结果解释

R1学习在现有奖励下恶化交付，G5改善区间跨零；容量队列优于持平而劣于趋势。联合配给实验出现库存策略排序反转。以上失败与局部证据均保留，不能以实验数量替代行为识别。
