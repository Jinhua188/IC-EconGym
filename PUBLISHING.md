# GitHub 发布

代码仓库与 GitHub Pages 项目页同时发布。已包含自动自检和 Pages 工作流。

## 发布步骤

在仓库外或仓库根目录使用 GitHub CLI：

```powershell
gh auth login --hostname github.com --git-protocol https --web
gh api user --jq .login
```

新建公开仓库时，从仓库根目录运行下列命令，将 OWNER 替换为自己的账号；已存在仓库应先读取远程记录并合并，不要强制覆盖。

```powershell
git init -b main
git config user.name "你的作者姓名或 GitHub 用户名"
git config user.email "你的 GitHub 已验证邮箱或 noreply 邮箱"
git add .
git commit -m "Publish IC-EconGym v0.2.0 research testbed"
gh repo create OWNER/IC-EconGym --public --source . --remote origin
gh api --method POST repos/OWNER/IC-EconGym/pages -f build_type=workflow
git push -u origin main
```

若 Pages 已启用，使用 PATCH 更新 `build_type=workflow`。在仓库 Settings → Pages 中确认 Source 为 GitHub Actions。工作流成功后的默认地址为 `https://OWNER.github.io/IC-EconGym/`。第一次部署必须以实际 Actions 状态与页面 HTTP 检查确认。

README 中没有伪造论文接受信息、作者、DOI 或 arXiv 链接。作者可在确定后补充作者单位与引用信息。网页使用 MathJax 和 Mermaid CDN 渲染数学及流程图，离线阅读时图表 PNG 与 Markdown 仍可使用。


已发布页面中的 Markdown 与图表在推送后自动重建；静态 PDF 须从最新论文页面打印更新，并写回 paper/IC-EconGym_中文论文完善稿.pdf。
