# Conventions for Code Generation

## Core Principles
- **KISS** - simple solutions, no over-engineering
- **DRY** - avoid code duplication
- **Readability first** - clear code over clever tricks
- **Minimal abstractions** - only what's necessary

Full philosophy and architecture details: @doc/vision.md (sections "Принципы разработки", "Архитектура")

## Code Standards

### Python
- **PEP 8** style
- **Type hints** required for function parameters and returns
- **Python 3.11+** features allowed
- **Russian** for user-facing messages, code, comments, docstrings

### Structure
- **Flat** - avoid deep nesting (see @doc/vision.md "Структура проекта")
- **Modular** - one responsibility per file
- **Simple** - understandable at first glance

### Error Handling
- `try-except` around critical operations
- **Log errors** with details (see @doc/vision.md "Логгирование")
- **User messages** - friendly, no technical details
- No retry logic (except LLM as per @doc/vision.md "Retry при ошибках")

## Configuration
- All settings via `.env` file (see @doc/vision.md "Конфигурирование")
- Use `os.getenv()` for access
- No validation - let it fail early if missing

## Dependencies
- Minimal external packages (see @doc/vision.md "Управление зависимостями")
- Only popular, proven libraries
- Pin versions in `pyproject.toml`

## Testing
- `pytest` for tests
- Focus on critical scenarios (see @doc/vision.md "Тестирование")
- Test what can break, skip trivial code

## Code Organization

### Main files (see @doc/vision.md "Архитектура проекта")
- `bot.py` - entry point, initialization
- `handlers.py` - command and message handlers
- `llm.py` - OpenRouter integration via OpenAI client

### Data storage
- In-memory dicts/lists (see @doc/vision.md "Модель данных")
- No database for MVP
- History format: `{chat_id: [{"role": "user"|"assistant", "content": "text"}]}`

### Prompts
- System prompt in `.env` as `SYSTEM_PROMPT` variable
- Load from env at startup

## Project-Specific

### LLM Integration
- OpenRouter via OpenAI SDK (see @doc/vision.md "Работа с LLM")
- Config via env vars: `LLM_MODEL`, `LLM_TEMPERATURE`, `LLM_MAX_TOKENS`
- Retry logic: `LLM_RETRY_ATTEMPTS` times with 1s pause

### Telegram Bot
- Use `aiogram` (async)
- Handle `/start` command
- Reject non-text messages with friendly message (see @doc/vision.md "Сценарии работы")

### Logging
- Python's `logging` module
- Level via `LOG_LEVEL` env var
- Log to stdout (Docker collects automatically)
- INFO: normal events, ERROR: with traceback (see @doc/vision.md "Логгирование")

## Development Workflow
- Use `uv` for dependencies
- `Makefile` for automation (install, test, build, up, down, logs)
- Docker for deployment (see @doc/vision.md "Деплой")

---

**References**: Full technical details in @doc/vision.md

