# 来源、归属与许可范围

本项目参考 EconGym 的任务组织和接口设计，参考 WonderEcon 的结果浏览方式。现有来源说明记录未复制两个仓库的网页素材或整套实现。

- EconGym：https://github.com/Miracle1207/EconGym
- WonderEcon：https://github.com/Planet-300894/WonderEcon

`install_into_econgym.py` 在用户独立取得的上游工作副本中安装扩展；本仓库不分发上游实现。引用上游项目不授予其代码或素材的许可，也不表示隶属或背书。

## 本次许可变更

治理整合前，本仓库尚未指定统一许可证。本次仅对 [LICENSE_SCOPE.md](LICENSE_SCOPE.md) 列明的项目原创代码及运行文档采用 Apache-2.0。第三方资料、处理后数据、权重、实验产物和论文按各自类别处理，不以根目录 LICENSE 推定获得许可。

## 外部数据与文献

- 投入产出原始工作簿、收入分劈依据和用户提供的未公开研究文件：不随本仓库发布；处理矩阵及来源记录见 `DATA_PROVENANCE.json`、`calibration/`。处理后公开记录的再分发权利仍需确认。
- AI 指标工作簿：原始附件不分发。聚合表和处理后的企业指标保留来源与年份限制；公开访问不代表原始数据或衍生表已获得开放数据许可。
- 中芯国际季度公告：保留官方来源链接、文件哈希、页码和提取数值，见 `external_validation/source_manifest.json`。下载的原始公告存于忽略目录，不进入发布包；提取数据的适用条款仍需审查。
- 论文中的引文、第三方方法与证据：见 `paper/references.bib` 和 `paper/reference_evidence.json`，本文不改变原来源的权利。
- Python 依赖、PyTorch、GitHub Actions、MathJax、Mermaid 等工具按其各自许可使用；本仓库不以 Apache-2.0 改变这些依赖的许可。
- `scripts_ic.check_governance` 从 Citation File Format 上游 1.2.0 固定提交读取 JSON Schema 做验证；schema 不随本仓库分发。上游采用 CC-BY-4.0：https://github.com/citation-file-format/citation-file-format/tree/396f738fb025b1d8acdb02a56ffc923f95dc8999 。

逐类权利状态见 [RIGHTS_REGISTRY.csv](RIGHTS_REGISTRY.csv)。待审查不等于权利已获确认；正式发布须完成这些类别的审查，或从归档中移除无权分发的文件。已有公开文件不因本声明而自动完成授权。
