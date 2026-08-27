<p align="center"><img src="docs/assets/agent-ecosystem-banner.svg" alt="Архитектура Agent Ecosystem" width="100%"></p>

# Agent Ecosystem

[Русский](README.md) · [English](README.en.md) · [简体中文](README.zh-CN.md)

Набор оригинальных скиллов, субагентов, общих правил и скриптов, который
работает через единый глобальный каталог `~/.agents`. Вы выбираете только
нужные профили и подключаете их к Codex, Claude Code, Gemini, Koda,
Yandex SourceCraft или другому
агенту.

Репозиторий не содержит весов моделей, секретов, виртуальных окружений,
кэшей и перепубликованных скиллов с неясной лицензией.

## Что вы получите

- 23 маркетинговых скилла: исследования, позиционирование, тексты, email,
  реклама, контент, CRO и запуск кампаний;
- естественный стиль текста без канцелярита и шаблонных фраз;
- UI/UX-процесс от пользовательского сценария до дизайн-системы;
- планирование и разработку видео на React и Remotion;
- context engineering для компактных промптов и передачи задач;
- CEO и специалистов по разработке, QA, маркетингу, продажам, SEO, дизайну,
  видео, контексту, продукту, юридическим рискам контента и безопасности diff;
- безопасный выборочный установщик, диагностику и адаптеры для разных агентов;
- инструкции и скрипты для локального MLX без весов моделей.

## Установка на новый компьютер

Нужны Git и Python 3. На macOS/Linux/WSL используется Bash, на Windows — PowerShell.

```bash
git clone https://github.com/bearatol/agent-ecosystem.git
cd agent-ecosystem
./scripts/bootstrap.sh
```

Windows PowerShell:

```powershell
git clone https://github.com/bearatol/agent-ecosystem.git
Set-Location agent-ecosystem
.\scripts\bootstrap.ps1 -Profile core,marketing -HostName codex,koda,sourcecraft
.\scripts\doctor.ps1
```

Интерактивный установщик покажет профили, спросит, что установить, и предложит
подключить выбранные AI-инструменты. По умолчанию файлы устанавливаются в
`~/.agents`.

Автоматическая установка без вопросов:

```bash
./scripts/install.sh \
  --profile core \
  --profile marketing \
  --host codex \
  --host claude
```

Проверка после установки:

```bash
./scripts/doctor.sh
```

## Можно поручить установку агенту

После клонирования отправьте любому агенту этот запрос:

```text
Read CONNECT.md in this repository. Help me choose the smallest profiles for
my work, install them into ~/.agents, connect my agent hosts, and run doctor.
Do not overwrite existing files without asking.
```

Агент прочитает каталог, предложит минимальный набор и покажет команду до её
выполнения.

## Профили

| Профиль | Содержимое |
| --- | --- |
| `core` | CEO, роутинг, поиск скиллов, правила и естественный текст |
| `marketing` | 23 маркетинговых скилла и субагент-маркетолог |
| `design` | UI/UX skill и дизайн-ревьюер |
| `video` | Remotion skill и видеопродюсер |
| `context` | Context engineering skill и субагент |
| `software` | Engineer, QA reviewer, software delivery и quality review |
| `content` | Product editor и набор скиллов для документации и контента |
| `local-models` | Только описание и MLX-скрипты, без моделей |
| `all` | Все поддерживаемые профили |

Посмотреть точный состав:

```bash
./scripts/list.sh
./scripts/list.sh --profile marketing
```

Можно поставить один компонент:

```bash
./scripts/install.sh --component skill:copywriting
```

## CEO и субагенты

CEO читает каталог, применяет собственные skills, разбивает цель на задания и
рекомендует подходящих специалистов. Рекомендации skills не обязательны:
каждый субагент самостоятельно выбирает все нужные ему skills в пределах своей
задачи и прав, а затем сообщает, что рассмотрел и применил.

Security reviewer намеренно изолирован от дополнительных skills, чтобы
проверяемый компонент не мог ослабить контролирующий его механизм.

```bash
~/.agents/tools/team/team.sh list --type agent
~/.agents/tools/team/team.sh recommend --tags software,quality
~/.agents/tools/team/team.sh plan \
  --goal "Подготовить проверенный релиз" \
  --tags software,quality,release
```

CEO передаёт задания через нативный механизм субагентов выбранного AI-хоста.
Субагенты не создают вложенных субагентов: если нужен другой специалист, запрос
возвращается CEO. Подробнее: [архитектура](docs/ARCHITECTURE.md) и
[протокол оркестрации](docs/ORCHESTRATION.md).

## Подключение AI-инструментов

```bash
./scripts/connect.sh --host codex
./scripts/connect.sh --host claude
./scripts/connect.sh --host gemini
./scripts/connect.sh --host koda
./scripts/connect.sh --host sourcecraft
```

Адаптеры создают ссылки на установленные скиллы. Они не перезаписывают
глобальные правила конкретного инструмента и создают безопасные обёртки
субагентов. Для другого агента укажите ему файлы `~/.agents/AGENTS.md` и
`~/.agents/CONNECT.md`. См. [матрицу хостов](docs/HOSTS.md), включая Windows и WSL.

## Обновление

```bash
git fetch origin
git log --oneline HEAD..'@{u}'
./scripts/update.sh APPROVED_40_CHARACTER_COMMIT
```

В Windows сначала проверьте тот же коммит, затем выполните
`./scripts/update.ps1 -ApprovedCommit APPROVED_40_CHARACTER_COMMIT`.
Скрипт обновления не запускает полученный из сети код, пока вы явно не подтвердите
точный upstream-коммит. Установщик не перезаписывает изменённые пользователем
или неуправляемые файлы, а сообщает конфликт для ручного решения.

При миграции со старой установки используйте `--preserve-agents-file`: компоненты
и каталог обновятся, а личный `~/.agents/AGENTS.md` сохранится. `--force`
принимается для совместимости команд, но не отключает защиту конфликтов.

## Локальные модели

Профиль `local-models` устанавливает только документацию и безопасные
loopback-скрипты. Веса и `.venv` не попадают в репозиторий.

```bash
./scripts/install.sh --profile local-models
cd ~/.agents/local-models/mlx-local-runtime
./setup.sh --version VERIFIED_VERSION
./run.sh --model /absolute/path/to/model --port 9944
```

MLX helper предназначен для Mac с Apple Silicon. Установку Python-пакетов и
загрузку модели пользователь запускает отдельно.

## Структура

```text
catalog/          единый каталог компонентов
library/skills/   оригинальные скиллы
library/agents/   промпты субагентов
library/rules/    общие правила
library/models/   описания и установочные скрипты
library/tools/    локальные инструменты каталога и координации
library/orchestration/ схемы заданий, результатов и состояния
profiles/         готовые подборки
docs/             архитектура, оркестрация и поддержка AI-хостов
examples/         проверяемые примеры пакетов задач и результатов
scripts/          установка, подключение, обновление и doctor
tests/            изолированная проверка установки
```

## Безопасность и лицензии

Содержимое репозитория создано специально для проекта и опубликовано под MIT.
Сторонние материалы нельзя добавлять без проверки права на распространение.
Удаление чужой лицензии или небольшая переработка текста не делает материал
оригинальным.

Установщик не загружает модели, не запускает сетевые сервисы автоматически и
не перезаписывает конфликтующие пользовательские файлы без `--force`. Подробнее:
[SECURITY.md](SECURITY.md) и [THIRD_PARTY.md](THIRD_PARTY.md).

## Участие в разработке

Новый компонент должен быть на английском языке, иметь запись в каталоге,
входить хотя бы в один профиль и проходить:

```bash
./tests/test.sh
./scripts/doctor.sh
git diff --check
```

См. [CONTRIBUTING.md](CONTRIBUTING.md). Лицензия: [MIT](LICENSE).
