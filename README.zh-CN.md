<p align="center"><img src="docs/assets/agent-ecosystem-banner.svg" alt=".agents 架构横幅" width="100%"></p>

# .agents

[Русский](README.md) · [English](README.en.md) · [简体中文](README.zh-CN.md)

这是一个可移植的 AI 代理工作层：把共享规则、必要技能和专业代理放在合适的位置，不用为每个任务从头拼装上下文。

先选择一个工作包。Foundation 会随它安装，并连接到你选定的 AI 工具。

## 快速开始

需要 Git 和 Python 3。在 macOS、Linux 或 WSL 上运行：

```bash
git clone https://github.com/bearatol/.agents.git
cd .agents
./scripts/bootstrap.sh
```

安装器只需要两个选择：工作包和主机。它会加入 Foundation（技术配置名为 `core`），安装工作包并提供连接。然后验证安装：

```bash
./scripts/doctor.sh
```

在 Windows 上使用 PowerShell：

```powershell
git clone https://github.com/bearatol/.agents.git
Set-Location .agents
.\scripts\install.ps1 -Profile core,software -HostName codex
.\scripts\doctor.ps1
```

## 选择工作包

Foundation 是共享基础：规则、CEO、路由、技能发现、上下文工程、自然写作和质量评审。为了保持命令兼容，`core` 仍然是它的技术名称。

| 你的目标 | 选择 |
| --- | --- |
| 开发和审查软件 | `software` |
| 市场研究、营销和发布 | `marketing` |
| 编写文档、文章和产品文案 | `content` |
| 设计界面 | `design` |
| 规划和制作视频 | `video` |
| 处理大型任务和上下文交接 | `context` |
| 配置不含模型权重的本地 MLX helper | `local-models` |

安装前可查看准确内容：

```bash
./scripts/list.sh --profile software
```

## 连接和验证

支持 Codex、Claude Code、Gemini、Koda、Yandex SourceCraft 和通用模式。快速开始会连接所选主机；之后可增加其他主机：

```bash
./scripts/connect.sh --host claude
./scripts/doctor.sh
```

适配器会为已安装技能创建受管理的链接，不会替换现有用户指令。Windows、WSL 和其他细节请查看[主机支持](docs/HOSTS.md)。

## 让上下文保持聚焦

Foundation 将精简的共享规则保存在一个地方。工作包只添加领域相关指令；CEO 可以把复杂目标拆成可验证的专业任务。每个结果都应说明完成内容、验证、所用技能和剩余风险。

这是一种工作方式，不承诺固定的 token 节省或通用质量；结果仍取决于任务、模型和审查。

## 需要更多控制时

<details>
<summary>非交互式安装和单个组件</summary>

```bash
./scripts/install.sh --profile core --profile marketing --host codex
./scripts/install.sh --component skill:copywriting
```

运行 `./scripts/list.sh` 查看所有维护中的配置。`all` 适合确实需要整个集合的情况。
</details>

<details>
<summary>CEO 与子代理</summary>

CEO 会拆分目标并推荐专家；每位专家都在任务和权限范围内选择技能。安全审查代理与可选技能隔离。详见[架构](docs/ARCHITECTURE.md)和[编排](docs/ORCHESTRATION.md)。

```bash
~/.agents/tools/team/team.sh recommend --tags software,quality
```
</details>

<details>
<summary>更新、本地模型和贡献</summary>

更新前先审查准确的 upstream 提交，再运行：

```bash
./scripts/update.sh APPROVED_40_CHARACTER_COMMIT
```

`local-models` 只安装文档和仅限 loopback 的 helpers，不安装模型权重或虚拟环境。更新、安全、许可证和贡献规则请查看 [CONNECT.md](CONNECT.md)、[SECURITY.md](SECURITY.md)、[THIRD_PARTY.md](THIRD_PARTY.md) 和 [CONTRIBUTING.md](CONTRIBUTING.md)。
</details>

仓库组件为本项目原创，并使用 [MIT](LICENSE) 许可证发布。
