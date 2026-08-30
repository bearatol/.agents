<p align="center"><img src="docs/assets/agent-ecosystem-banner.svg" alt="Архитектура .agents" width="100%"></p>

# .agents

<p align="center">
  <a href="https://github.com/bearatol/.agents/actions/workflows/test.yml"><img alt="Tests" src="https://github.com/bearatol/.agents/actions/workflows/test.yml/badge.svg"></a>
  <a href="LICENSE"><img alt="MIT License" src="https://img.shields.io/badge/license-MIT-blue.svg"></a>
</p>

<p align="center"><strong>Ваши наработки для нейросетей — в одном переносимом месте. Используйте их в Codex, Claude, Gemini, Kimi и других инструментах по отдельности или вместе.</strong></p>

[Русский](README.md) · [English](README.en.md) · [简体中文](README.zh-CN.md)

`.agents` — это Git-хранилище общих правил, skills, специалистов, промтов, настроек моделей и совместных задач. AI-приложения подключаются к нему как сменные адаптеры: можно заменить один инструмент другим или поручить разную работу нескольким одновременно. Существующие пользовательские файлы не перезаписываются молча.

## Быстрый старт

Нужны Git и Python 3. На macOS, Linux или WSL:

```bash
git clone https://github.com/bearatol/.agents.git
cd .agents
./scripts/agents.sh setup
```

На Windows:

```powershell
git clone https://github.com/bearatol/.agents.git
Set-Location .agents
.\scripts\agents.ps1 setup
```

Установка спрашивает, для каких задач вам нужны помощники и какое AI-приложение вы используете. Можно выбрать несколько пунктов, например «код и видео». Перед изменениями вы увидите понятное подтверждение.

## Несколько направлений или всё

Если вы не хотите отвечать на вопросы, укажите задачи прямо в команде. Например, для кода и видео:

```bash
./scripts/agents.sh setup --work code --work video --app codex
```

На Windows:

```powershell
.\scripts\agents.ps1 setup -Work code,video -App codex
```

Чтобы установить всё:

```bash
./scripts/agents.sh setup --work all --app codex
```

Чтобы Codex, Claude, Gemini и Kimi одновременно использовали одну среду:

```bash
./scripts/agents.sh setup --work all \
  --app codex --app claude --app gemini --app kimi
```

На Windows передайте список через запятую: `-App codex,claude,gemini,kimi`.

## Основные команды

| Задача | macOS / Linux / WSL | Windows |
| --- | --- | --- |
| Установить или дополнить среду | `./scripts/agents.sh setup` | `.\scripts\agents.ps1 setup` |
| Посмотреть текущее состояние | `./scripts/agents.sh status` | `.\scripts\agents.ps1 status` |
| Сохранить переносимую конфигурацию | `./scripts/agents.sh export ./agents.lock.json` | `.\scripts\agents.ps1 export .\agents.lock.json` |
| Восстановить её на новом компьютере | `./scripts/agents.sh restore ./agents.lock.json` | `.\scripts\agents.ps1 restore .\agents.lock.json` |
| Полностью проверить установку | `./scripts/agents.sh doctor` | `.\scripts\agents.ps1 doctor` |

Личные наработки добавляются в переносимую библиотеку:

```bash
./scripts/agents.sh library add skill my-skill ./my-skill
./scripts/agents.sh library list
./scripts/agents.sh library trust skill my-skill
./scripts/agents.sh library activate skill my-skill
./scripts/agents.sh connect codex claude gemini kimi
./scripts/agents.sh library check
```

Вместо `skill` можно указать `rule`, `prompt`, `agent`, `mcp`, `model` или новое имя, которого сегодня ещё не существует. Новый тип — просто новая папка. Импорт не включается автоматически: сначала проверьте его, затем явно отметьте доверенным. В текущей версии `activate` публикует skills; остальные типы уже безопасно хранятся и ждут соответствующих адаптеров.

## Несколько AI работают как команда

Общие настройки лежат в `.agents`, а задания и ответы разных AI не перезаписывают друг друга. Например, Claude выполняет задачу, Gemini и Kimi проверяют, Codex принимает итог:

```bash
./scripts/agents.sh team init release \
  --objective "Подготовить выпуск" --coordinator codex \
  --member claude --member gemini --member kimi

./scripts/agents.sh team task release implementation \
  --title "Сделать изменение" --objective "Подготовить проверенный результат" \
  --role engineer --worker claude --reviewer gemini --reviewer kimi \
  --scope scripts --accept "Все тесты проходят"

./scripts/agents.sh team status release
```

Файлы проекта находятся в `workspace/projects/release/`. Их можно читать из любого AI-приложения или синхронизировать через Git. Полный сценарий результата, проверок и принятия: [совместная работа](docs/WORKSPACE.md).

Старые `install`, `connect`, `update` и `list` остаются доступны для автоматизации и точной настройки, но для обычной работы они не нужны.

## Первое полезное действие

После setup откройте или перезапустите выбранный AI-инструмент и дайте ему обычную задачу:

> Проверь этот проект на ошибки. Сначала составь короткий план, затем внеси только согласованные изменения и покажи результаты тестов.

Для большой многопрофильной задачи:

> Проведи полный аудит продукта с помощью CEO. Подключай специалистов только там, где они действительно нужны, и верни доказательства по каждому выводу.

## Перенос на новый компьютер

На старом компьютере:

Экспортируйте из доверенного checkout без незакоммиченных изменений, чтобы содержимое точно соответствовало commit в lock-файле.

```bash
./scripts/agents.sh status
./scripts/agents.sh export ./agents.lock.json
```

Скопируйте `agents.lock.json` на новый компьютер, клонируйте репозиторий и отдельно проверьте указанный в lock-файле полный commit SHA. Переключите чистый checkout без локальных изменений на этот уже проверенный commit, затем выполните:

```bash
./scripts/agents.sh restore ./agents.lock.json
./scripts/agents.sh doctor
```

Restore сам не выполняет `fetch`, `checkout`, downgrade или удаление. Сначала он валидирует lock-файл и все места назначения; при конфликте останавливается до постоянных записей. Подробный сценарий: [переносимость и восстановление](docs/PORTABILITY.md).

| Переносится | Не переносится |
| --- | --- |
| Выбранные профили и отдельные компоненты | Аккаунты и авторизация |
| Подключения к поддерживаемым хостам | API-ключи и другие секреты |
| Точный commit и версия экосистемы | Сами AI-приложения и CLI-пакеты |
| Общая личная библиотека и командные проекты | Веса моделей, плагины и посторонние dotfiles |

Личная библиотека переносится самим Git-репозиторием; lock-файл восстанавливает установленную среду и подключения. Для личных материалов создайте свой приватный репозиторий. Никогда не сохраняйте в нём пароли, ключи и сессии: автоматическая проверка помогает, но не заменяет просмотр изменений перед push.

## Что означает status

- `current` — установленная копия соответствует источнику;
- `missing` — управляемый объект отсутствует;
- `managed-stale` — источник обновился, установленная копия ещё старая;
- `locally-modified` — установленный объект изменён пользователем;
- `host-conflicting` — подключение хоста отсутствует или занято чужим объектом.

`status` показывает состояние установленной среды. `doctor` дополнительно проверяет каталог, профили, структуру репозитория, запрещённые артефакты и интеграцию хостов. Небезопасное или неполное состояние возвращает ненулевой код.

## Что выбрать

| Если вы хотите… | Выберите при установке |
| --- | --- |
| Разрабатывать и проверять код | «Код» |
| Исследовать рынок, делать маркетинг и запуски | «Исследования и маркетинг» |
| Писать документацию, статьи и продуктовые тексты | «Тексты и документы» |
| Проектировать интерфейсы | «Дизайн интерфейсов» |
| Планировать и делать видео | «Видео» |
| Работать с большими задачами и передачей контекста | «Сложные задачи» |
| Использовать локального AI-помощника | «Локальный AI» |

Общие правила безопасности, проверки качества и базовые помощники добавляются автоматически. Вам не нужно разбираться в их внутреннем устройстве.

## Безопасность и устройство

Lock-файл содержит только версию схемы, версию экосистемы, полный commit SHA, профили, компоненты и хосты. В нём нет путей, команд, URL, переменных окружения, credentials или содержимого файлов. Локальные изменения и неуправляемые файлы сохраняются; конфликт требует явного решения.

Подробнее: [личная библиотека и команда AI](docs/WORKSPACE.md) · [хосты](docs/HOSTS.md) · [архитектура](docs/ARCHITECTURE.md) · [планы](docs/ROADMAP.md) · [безопасность](SECURITY.md) · [вклад](CONTRIBUTING.md).

Проект распространяется под лицензией [MIT](LICENSE).
