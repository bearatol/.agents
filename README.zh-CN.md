# Agent Ecosystem

[Русский](README.md) · [English](README.en.md) · [简体中文](README.zh-CN.md)

这是一个原创的 AI 技能、子代理、共享规则和安装脚本工具包。所有组件统一
安装到全局目录 `~/.agents`，你可以只选择工作需要的配置，并连接到 Codex、
Claude Code、Gemini 或其他 AI 代理。

本仓库不包含模型权重、密钥、虚拟环境、缓存，也不重新发布授权不明确的技能。

## 包含内容

- 23 个营销技能：市场研究、定位、文案、邮件、广告、内容、CRO 和活动发布；
- 自然写作流程，用于删除官僚化、空洞和模板化表达；
- 从用户流程到设计系统的 UI/UX 工作方法；
- 使用 React 和 Remotion 规划与开发视频；
- 用于精简提示词和可靠交接的上下文工程；
- CEO、营销、设计评审、视频制作、上下文工程、工程师、QA 和产品编辑子代理；
- 不会静默覆盖文件的选择性安装器、诊断工具和主机适配器；
- 不含模型权重的本地 MLX 文档和辅助脚本。

## 在新电脑上安装

需要 Git、Bash、Python 3，以及 macOS 或 Linux。

```bash
git clone https://github.com/bearatol/agent-ecosystem.git
cd agent-ecosystem
./scripts/bootstrap.sh
```

交互式安装器会显示可用配置，询问需要安装的内容，并允许连接所选 AI 工具。
默认安装目录是 `~/.agents`。

无需交互的安装方式：

```bash
./scripts/install.sh \
  --profile core \
  --profile marketing \
  --host codex \
  --host claude
```

安装后运行检查：

```bash
./scripts/doctor.sh
```

## 让 AI 代理完成安装

克隆仓库后，将下面的请求发送给任意代理：

```text
Read CONNECT.md in this repository. Help me choose the smallest profiles for
my work, install them into ~/.agents, connect my agent hosts, and run doctor.
Do not overwrite existing files without asking.
```

代理应先读取目录，推荐满足需求的最小组件集合，并在执行前显示完整命令。

## 配置列表

| 配置 | 内容 |
| --- | --- |
| `core` | CEO、路由、技能发现、共享规则和自然写作 |
| `marketing` | 23 个营销技能和营销子代理 |
| `design` | UI/UX 技能和设计评审子代理 |
| `video` | Remotion 技能和视频制作子代理 |
| `context` | 上下文工程技能和子代理 |
| `software` | 工程师、QA、软件交付和质量评审 |
| `content` | 产品编辑以及文档和内容技能 |
| `local-models` | 仅文档和 MLX 脚本，不含模型 |
| `all` | 所有维护中的配置 |

查看具体内容：

```bash
./scripts/list.sh
./scripts/list.sh --profile marketing
```

只安装一个组件：

```bash
./scripts/install.sh --component skill:copywriting
```

## CEO 与子代理

CEO 读取目录、应用自身需要的技能、拆分目标并推荐专业子代理。技能推荐只是建议：
每个子代理会在任务范围和权限内独立选择所有有用技能，并在结果中报告考虑和实际
应用的技能。

安全评审代理会与可选技能保持隔离，避免被评审的组件削弱评审它的控制机制。

```bash
~/.agents/tools/team/team.sh list --type agent
~/.agents/tools/team/team.sh recommend --tags software,quality
~/.agents/tools/team/team.sh plan \
  --goal "准备经过验证的发布" \
  --tags software,quality,release
```

CEO 通过所选 AI 工具的原生子代理机制派发任务。子代理不能继续创建子代理；如果
需要其他专家，必须将请求返回 CEO。详见[架构](docs/ARCHITECTURE.md)和
[编排协议](docs/ORCHESTRATION.md)。

## 连接 AI 工具

```bash
./scripts/connect.sh --host codex
./scripts/connect.sh --host claude
./scripts/connect.sh --host gemini
```

适配器为技能创建链接，并生成符合不同工具格式的子代理包装文件。它不会覆盖工具
自身的全局规则文件。对于其他工具，请让代理读取 `~/.agents/AGENTS.md` 和
`~/.agents/CONNECT.md`。参见[主机支持](docs/HOSTS.md)。

## 更新

```bash
./scripts/update.sh
```

安装器不会静默替换已修改的文件，而是报告冲突。只有在明确需要覆盖时才使用
`--force`，并建议先用 Git 保存个人修改。

从旧版本迁移时，可将 `--preserve-agents-file` 与 `--force` 一起使用：
组件和目录会更新，但个人的 `~/.agents/AGENTS.md` 会保留。

## 本地模型

`local-models` 配置只安装文档和仅监听本机回环地址的辅助脚本，不包含模型权重
或 `.venv`。

```bash
./scripts/install.sh --profile local-models
cd ~/.agents/local-models/mlx-local-runtime
./setup.sh --version VERIFIED_VERSION
./run.sh --model /absolute/path/to/model --port 9944
```

MLX 辅助脚本适用于 Apple Silicon Mac。安装 Python 包和下载模型都必须由用户
单独、明确地执行。

## 仓库结构

```text
catalog/          组件信息的唯一来源
library/skills/   原创技能
library/agents/   子代理提示词
library/rules/    共享规则
library/models/   文档和安装辅助脚本
library/tools/    本地目录与协调工具
library/orchestration/ 任务、结果和状态协议
profiles/         预设组件组合
docs/             架构、编排和 AI 工具支持
examples/         经过验证的任务与结果示例
scripts/          安装、连接、更新和诊断
tests/            隔离安装测试
```

## 安全与许可证

仓库内容为本项目原创，并使用 MIT 许可证发布。未经确认有再分发权，不得加入
第三方材料。删除许可证或只做表面修改，并不会使内容变成原创作品。

安装器不会下载模型、自动启动网络服务，也不会在没有 `--force` 的情况下覆盖
冲突文件。详见 [SECURITY.md](SECURITY.md) 和
[THIRD_PARTY.md](THIRD_PARTY.md)。

## 参与贡献

新组件必须使用英文，加入目录和至少一个配置，并通过：

```bash
./tests/test.sh
./scripts/doctor.sh
git diff --check
```

更多信息见 [CONTRIBUTING.md](CONTRIBUTING.md)。许可证：[MIT](LICENSE)。
