<p align="center"><img src="docs/assets/agent-ecosystem-banner.svg" alt="Архитектура .agents" width="100%"></p>

# .agents

[Русский](README.md) · [English](README.en.md) · [简体中文](README.zh-CN.md)

Один переносимый слой для работы с AI-агентами. Он даёт общие правила, нужные skills и специалистов там, где они действительно нужны, а не заставляет каждый раз собирать контекст с нуля.

Начните с одной рабочей подборки. Foundation устанавливается вместе с ней и подключает её к выбранному AI-инструменту.

## Быстрый старт

Нужны Git и Python 3. На macOS/Linux/WSL:

```bash
git clone https://github.com/bearatol/.agents.git
cd .agents
./scripts/bootstrap.sh
```

Установщик попросит только два выбора: рабочую подборку и хост. Он добавит Foundation (техническое имя профиля — `core`), установит подборку и предложит подключение. После этого проверьте установку:

```bash
./scripts/doctor.sh
```

На Windows используйте PowerShell:

```powershell
git clone https://github.com/bearatol/.agents.git
Set-Location .agents
.\scripts\install.ps1 -Profile core,software -HostName codex
.\scripts\doctor.ps1
```

## Что выбрать

Foundation — общая основа: правила, CEO, маршрутизация, поиск skills, контекстная инженерия, естественный текст и контроль качества. `core` остаётся его техническим именем для совместимости команд.

| Если вы хотите… | Выберите |
| --- | --- |
| Разрабатывать и проверять код | `software` |
| Исследовать рынок, делать маркетинг и запуски | `marketing` |
| Писать документацию, статьи и продуктовые тексты | `content` |
| Проектировать интерфейсы | `design` |
| Планировать и делать видео | `video` |
| Работать с большими задачами и передачей контекста | `context` |
| Настроить локальный MLX helper без весов моделей | `local-models` |

Можно увидеть точный состав до установки:

```bash
./scripts/list.sh --profile software
```

## Подключение и проверка

Поддерживаются Codex, Claude Code, Gemini, Koda, Yandex SourceCraft и универсальный режим. Быстрый старт подключает выбранный хост; позже можно добавить другой:

```bash
./scripts/connect.sh --host claude
./scripts/doctor.sh
```

Адаптеры создают управляемые ссылки на установленные skills и не заменяют существующие пользовательские инструкции. Подробности и особенности Windows/WSL: [матрица хостов](docs/HOSTS.md).

## Как это помогает не раздувать контекст

Foundation хранит короткие общие правила в одном месте. Рабочая подборка добавляет только профильные инструкции, а CEO может разделить сложную цель на проверяемые задачи для специалистов. Каждый результат должен возвращать сделанное, проверку, применённые skills и остаточные риски.

Это организационный подход, а не обещание фиксированной экономии токенов или универсального качества: итог зависит от задачи, модели и проверки результата.

## Когда нужно больше контроля

<details>
<summary>Установка без вопросов и отдельные компоненты</summary>

```bash
./scripts/install.sh --profile core --profile marketing --host codex
./scripts/install.sh --component skill:copywriting
```

Посмотреть все поддерживаемые профили: `./scripts/list.sh`. Профиль `all` предназначен для тех, кому действительно нужен весь набор.
</details>

<details>
<summary>Работа через CEO и субагентов</summary>

CEO разбивает цель на задания и рекомендует подходящих специалистов; каждый специалист сам выбирает skills в пределах задачи и прав. Безопасностный ревьюер изолирован от необязательных skills. См. [архитектуру](docs/ARCHITECTURE.md) и [протокол оркестрации](docs/ORCHESTRATION.md).

```bash
~/.agents/tools/team/team.sh recommend --tags software,quality
```
</details>

<details>
<summary>Обновление, локальные модели и вклад в проект</summary>

Перед обновлением проверьте точный upstream-коммит, затем выполните:

```bash
./scripts/update.sh APPROVED_40_CHARACTER_COMMIT
```

`local-models` устанавливает документацию и loopback-only helpers, но не веса моделей и не виртуальное окружение. Для правил обновления, безопасности, лицензий и вклада в проект см. [CONNECT.md](CONNECT.md), [SECURITY.md](SECURITY.md), [THIRD_PARTY.md](THIRD_PARTY.md) и [CONTRIBUTING.md](CONTRIBUTING.md).
</details>

Репозиторий содержит оригинальные компоненты проекта под лицензией [MIT](LICENSE).
