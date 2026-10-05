# GitHub 与研究软件发布

## 当前阶段

仓库：https://github.com/Jinhua188/IC-EconGym 。项目页：https://jinhua188.github.io/IC-EconGym/ 。v0.2.0 为既有发布；`VERSION=0.3.0` 为待发布版本线。本次治理整合不创建 v0.3.0 标签、GitHub Release 或 DOI。

## 治理整合与验证

变更通过分支和 PR 合入 `main`。先运行：

```bash
python -m pip install -r requirements_ic.txt -r requirements_governance.txt
python validate_extension.py
python -m scripts_ic.check_governance
```

学习环境另安装 `requirements_learning.lock.txt`，执行 `python -m scripts_ic.verify_upgrade`。这检查检查点身份、划分隔离、适配和队列，不重新训练。修改模型或实验协议时须重跑受影响的实验；本次治理变更保留既有科学结果。

`Validate environment` 的 `validate` 和 `Governance and release checks` 的 `governance` 是分支检查。提交治理文件不等于已开启远程规则；以 Settings 和 `GITHUB_SETTINGS_CHECKLIST.md` 的实际核查记录为准。单维护者阶段不要求另一人批准，不自动添加协作者权限。

## 正式 v0.3.0 的人工确认项

在 `RELEASE_READINESS.json` 中记录最终作者确认、各类别公开产物的再分发审查、Zenodo 启用确认和发布授权的证据，不用自动检查代替人工权利判断。待这些项确认后才运行：

```bash
python -m scripts_ic.check_governance --publication
```

待确认项使此命令退出失败，这是预期行为。还须确认全部 Actions 成功、Pages 对应候选提交以及清洁工作树，再由 @Jinhua188 决定发布。

完整步骤见 [ZENODO_RELEASE_GUIDE.md](ZENODO_RELEASE_GUIDE.md) 和 [RELEASE_v0.3.0.md](RELEASE_v0.3.0.md)。GitHub/Zenodo 会归档整个提交；排除某类产物的代码许可不等于有权归档这些文件。确认权利或移除无权分发的内容后，才能发正式 Release。

## 标签与 DOI

v0.2.0 及后续已发布标签均保留原指向。DOI 由 Zenodo 实际归档后取得；回填 DOI 通过新 PR 更新 main，不移动已发布标签。不填写假作者、假 DOI 或论文接受状态。

## Pages

Pages 使用 GitHub Actions，推送 main 后构建。网页为已计算轨迹的静态回放。更新页面运行 `python -m scripts_ic.build_project_site`；论文 PDF 须随正文实际修订单独更新。当前工作流不因标签推送而部署网页。
