# AdvisorSkill

[English](README.md)

AdvisorSkill 将学术论文评注整理为可追溯的导师写作偏好。宿主 Agent 根据证据起草变更提案，学生作出审核决定，Python CLI 验证记录并把已批准的规则构建成可移植的 Agent Skill。

## 在 Windows 上运行

需要 Python 3.11 或以上版本。在项目根目录用 PowerShell 执行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[test]'
.\.venv\Scripts\python.exe -m advisorskill --help
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe scripts/demo.py
```

演示会在 `.advisorskill/` 下保留两轮合成反馈的工作区和两次构建产物，便于检查审批、拒绝、冲突和版本更新。

## 用自己的反馈创建 Profile

用 Codex 打开本仓库，即可按请求自动匹配 [advisor-builder](.agents/skills/advisor-builder/SKILL.md)。例如说「把这批导师评注保存到 `phy/sxz`」。已经选定档案的同一轮工作可以继续使用该档案。如果是首次收录，可以直接说「新建 `phy/sxz` 私有档案，再收录这些评注」。简称能唯一匹配时可直接使用，出现多个候选时会请你选择。

本地档案按 `.advisorskill/<学科>/<导师代号>/` 存放。[公共目录](registry/profiles/)使用相同的二级分类键。每个私有档案的 `state.json` 保存评注、规则和审核记录。收录具体段落的评注时，Agent 会从你提供或授权的稿件中保存对应原文，以及能核实的实际修改片段。构建后的 Skill 按主题提供已审核的写作规则。

在已激活虚拟环境的终端中运行以下命令，将输入文件路径换成自己的私有文件。

```powershell
advisorskill init --id phy-sxz --discipline phy --workspace .advisorskill/phy/sxz
advisorskill ingest --workspace .advisorskill/phy/sxz --input PATH_TO_PRIVATE_COMMENTS.jsonl
advisorskill prepare --workspace .advisorskill/phy/sxz
```

请宿主 Agent 按 [advisor-builder](.agents/skills/advisor-builder/SKILL.md) 读取工作区里的 `prepare.json`，并将提案写入 `.advisorskill/phy/sxz/proposal.yaml`。先看差异，再选择批准或拒绝。

```powershell
advisorskill review --workspace .advisorskill/phy/sxz --proposal .advisorskill/phy/sxz/proposal.yaml
advisorskill apply --workspace .advisorskill/phy/sxz --proposal .advisorskill/phy/sxz/proposal.yaml --approve
advisorskill validate --workspace .advisorskill/phy/sxz
advisorskill build --workspace .advisorskill/phy/sxz --output dist/phy
```

拒绝时使用 `--reject`，决定会留在工作区供追溯。每轮导入后重新运行 `prepare`。构建结果位于 `dist/phy/advisor-phy-sxz/`，其中按主题列出当前可用规则。

原始评论、论文片段、提案和任务包均为私有数据。建议将工作区置于仓库外或已忽略的 `.advisorskill/`，并在分享前人工审查生成的规则。

## 分享公开指南

可以请 Agent「把 `phy/sxz` 的 R-001 和 R-003 做成公开指南草稿，给我审核」。审核具体内容、许可和投稿仓库后，Agent 可以把那份 Markdown 原样提交到 GitHub Issue。维护者审核合并后，公开指南集中在 `registry/profiles/<学科>/<导师>/GUIDE.md`。每位导师的本地写作 Skill 可以直接构建到当前论文项目的 `.agents/skills`（Codex）或 `.dsh/skills`（DSH）。

[公开分享和维护命令](docs/sharing.md) · [输入格式与提案协议](docs/protocol.md) · [合成输入示例](tests/fixtures) · [贡献指南](CONTRIBUTING.md)
