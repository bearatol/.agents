<p align="center"><img src="docs/assets/agent-ecosystem-banner.svg" alt=".agents 架构" width="100%"></p>

# .agents

<p align="center">
  <a href="https://github.com/bearatol/.agents/actions/workflows/test.yml"><img alt="Tests" src="https://github.com/bearatol/.agents/actions/workflows/test.yml/badge.svg"></a>
  <a href="LICENSE"><img alt="MIT License" src="https://img.shields.io/badge/license-MIT-blue.svg"></a>
</p>

<p align="center"><strong>只需配置一次 AI agent 工作空间，即可通过五个清晰的命令检查、迁移和恢复。</strong></p>

[Русский](README.md) · [English](README.en.md) · [简体中文](README.zh-CN.md)

`.agents` 管理共享规则、skills、专业 agents、工作配置和 Codex、Claude Code、Gemini CLI、Koda、SourceCraft 的连接。它不会静默覆盖已有的用户文件。

## 快速开始

需要 Git 和 Python 3。macOS、Linux 或 WSL：

```bash
git clone https://github.com/bearatol/.agents.git
cd .agents
./scripts/agents.sh setup
```

Windows：

```powershell
git clone https://github.com/bearatol/.agents.git
Set-Location .agents
.\scripts\agents.ps1 setup
```

安装会询问您希望 AI 帮您做什么，以及您使用哪个 AI 应用。可同时选择多个方向，例如“代码和视频”；在修改任何内容前会给出清晰确认。

## 组合多个工作配置或全部安装

如果不想回答问题，可以直接写出需要的工作方向。例如，代码和视频：

```bash
./scripts/agents.sh setup --work code --work video --app codex
```

Windows：

```powershell
.\scripts\agents.ps1 setup -Work code,video -App codex
```

如需全部安装：

```bash
./scripts/agents.sh setup --work all --app codex
```

## 五个主要命令

| 目标 | macOS / Linux / WSL | Windows |
| --- | --- | --- |
| 安装或扩展工作空间 | `./scripts/agents.sh setup` | `.\scripts\agents.ps1 setup` |
| 查看当前状态 | `./scripts/agents.sh status` | `.\scripts\agents.ps1 status` |
| 导出可迁移配置 | `./scripts/agents.sh export ./agents.lock.json` | `.\scripts\agents.ps1 export .\agents.lock.json` |
| 在新电脑恢复 | `./scripts/agents.sh restore ./agents.lock.json` | `.\scripts\agents.ps1 restore .\agents.lock.json` |
| 运行完整检查 | `./scripts/agents.sh doctor` | `.\scripts\agents.ps1 doctor` |

原有的 install、connect、update 和 list 脚本仍可用于自动化和高级控制。

## 第一个任务

Setup 完成后，打开或重启所选 AI 工具，然后直接提出任务：

> 检查这个项目中的错误。先给出简短计划，只进行已确认的修改，并展示测试结果。

大型任务可以使用 CEO：

> 使用 CEO 进行完整的产品审计。只在确有价值时调用专业 agents，并为每个结论提供证据。

## 迁移到新电脑

旧电脑：

请从可信且没有未提交更改的 checkout 导出，确保其内容与 lock 中记录的 commit 完全一致。

```bash
./scripts/agents.sh status
./scripts/agents.sh export ./agents.lock.json
```

复制 `agents.lock.json`，在新电脑克隆仓库，并单独检查 lock 中记录的完整 commit SHA。将没有本地更改的干净 checkout 切换到已经确认的 commit 后执行：

```bash
./scripts/agents.sh restore ./agents.lock.json
./scripts/agents.sh doctor
```

Restore 不会自动执行 fetch、checkout、降级、删除或强制覆盖。它先验证 lock 并预检所有目标。详见 [可迁移性与恢复](docs/PORTABILITY.md)。

| 会迁移 | 不会迁移 |
| --- | --- |
| 选定 profiles 和单独 components | 账号和身份验证 |
| 支持的 host 连接 | API keys 和其他 secrets |
| 精确 commit 和生态版本 | AI 应用和 CLI 软件包 |
| 受管理的 rules、skills 和 agents | 模型权重、plugins 和无关 dotfiles |

这不是整台电脑的备份，而是 `.agents` 受管理工作空间的恢复。

## 状态说明

- `current`：安装内容与来源一致；
- `missing`：受管理目标缺失；
- `managed-stale`：来源已更新，安装副本仍是旧版本；
- `locally-modified`：安装内容被本地修改；
- `host-conflicting`：host 连接缺失或被非管理内容占用。

`status` 检查安装状态。`doctor` 还会验证 catalog、profiles、仓库文本、禁止的文件和 host 集成；不安全或不完整的状态会返回非零退出码。

## 选择需要的帮助

| 目标 | 在安装时选择 |
| --- | --- |
| 软件开发与审查 | 代码 |
| 市场研究、营销与发布 | 研究与营销 |
| 文档和产品内容 | 写作 |
| 界面设计 | 设计 |
| 视频规划与制作 | 视频 |
| 长任务与上下文交接 | 复杂任务 |
| 本地 AI helper | 本地 AI |

共享的安全规则、质量检查和基础帮助会自动加入；无需了解它们的内部名称。

## 信任边界

Lock 仅包含 schema version、ecosystem version、完整 commit SHA、profiles、components 和 hosts；不包含路径、命令、URL、环境变量、credentials 或文件内容。本地修改和非管理文件会被保留，冲突需要用户明确处理。

更多信息：[hosts](docs/HOSTS.md) · [architecture](docs/ARCHITECTURE.md) · [orchestration](docs/ORCHESTRATION.md) · [security](SECURITY.md) · [contributing](CONTRIBUTING.md)。

本项目采用 [MIT License](LICENSE)。
