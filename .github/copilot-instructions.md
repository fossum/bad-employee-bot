# Bad Employee Discord Bot - AI Agent Instructions

## Project Overview
This is a Discord bot that responds sarcastically to programming-related trigger words using Google's Gemini AI. The bot maintains chat history in PostgreSQL and is deployed via Kubernetes with Helm charts managed by FluxCD.

## Architecture & Component Interaction

### Core Components
- **`main.py`**: Discord bot entry point with event handlers and command processing
- **`gemini_client.py`**: Wrapper for Google Gemini API with persona-based prompting
- **`chat_history.py`**: PostgreSQL persistence layer using context managers for connection management
- **Helm chart**: Located in `charts/bad-employee/`, uses TrueCharts common library (v25.4.10) with CloudNativePG for database

### Key Data Flow
1. Discord message arrives → `on_message()` event handler in `main.py`
2. Message saved to PostgreSQL via `ChatHelper.save_chat_message()`
3. If message contains trigger words (Perl, Python, COBAL, etc.), retrieve user's previous messages
4. Generate AI response with `GeminiClient.generate_response()` passing current message + history
5. Response sent back to Discord channel

## Critical Patterns & Conventions

### Context Manager Pattern for Database Access
Always use `ChatHelper` with context manager syntax:
```python
with ChatHelper(db_connection_params) as chat_helper:
    chat_helper.verify_table()
    chat_helper.save_chat_message(message)
```
Never instantiate without `with` - connection cleanup is handled in `__exit__`.

### Database Connection Parameters
Database credentials come from environment variables mapped in Helm chart:
- `BAD_EMPLOYEE_DB`, `BAD_EMPLOYEE_USER`, `BAD_EMPLOYEE_PASS` (from cnpg-app secret)
- `BAD_EMPLOYEE_HOST`, `BAD_EMPLOYEE_PORT`
- See `values.yaml` workload.main.podSpec.containers.main.env for the complete mapping

### AI Response Generation
The Gemini client uses a fixed personality defined in `PROMPT_BASIS` (snarky bad employee who prefers Python over Perl). When modifying bot personality:
1. Edit `GeminiClient.PROMPT_BASIS` constant
2. Test with functional tests in `test/ft_gemini_client.py`
3. Previous messages are formatted as CSV-like context: `timestamp,channel,message`

### Discord Bot Commands
- Use `commands.Bot` with prefix `!` (not raw `discord.Client`)
- Commands defined with `@bot.command()` decorator
- Always call `bot.process_commands(message)` at end of `on_message()` handler
- Bot ignores its own messages via `if message.author == bot.user: return`

## Development Workflows

### Local Development Setup
```bash
# 1. Set required environment variables in .env file:
GEMINI_API_KEY=<from https://aistudio.google.com/apikey>
DISCORD_APP_TOKEN=<from https://discord.com/developers/applications>
BAD_EMPLOYEE_DB=bad_employee
BAD_EMPLOYEE_USER=employee
BAD_EMPLOYEE_PASS=password
BAD_EMPLOYEE_HOST=db
BAD_EMPLOYEE_PORT=5432

# 2. Install dependencies
pipenv install --dev

# 3. Run the bot
pipenv run python main.py
```

### Testing
- Functional tests require `GEMINI_API_KEY` environment variable set
- Run tests: `pipenv run pytest test/ft_gemini_client.py`
- Tests use pytest-asyncio for async/await testing patterns

### Docker Build & Deployment
- Multi-stage build installs system dependencies (libpq-dev) for psycopg2
- Uses pipenv with `--system --deploy --ignore-pipfile` for deterministic builds
- CI/CD pushes to `ghcr.io/fossum/bad-employee-bot` on main branch commits
- Tags: `latest`, branch name, and git SHA (see `.github/workflows/docker-build.yml`)

### Helm Chart Management
- Chart version bumps in `charts/bad-employee/Chart.yaml` trigger Helm releases to GitHub Pages
- Dependencies fetched via `helm dependency build charts/bad-employee`
- CloudNativePG cluster auto-configured when `cnpg.main.enabled: true`
- FluxCD monitors the GitHub Pages Helm repository (see `kubernetes/helmrepository.yaml`)

## Project-Specific Gotchas

### PostgreSQL Schema Management
- Table created automatically on first connection via `verify_table()` in main.py
- Schema defined in `ChatHelper.TABLE_STRUCT` constant
- Use `sql.Identifier()` for table names to prevent SQL injection
- Message retrieval returns mock Discord objects, not real API objects (see `messages_from_user()`)

### Async Patterns
- Gemini API calls use `generate_content_async()` and `send_message_async()`
- Discord event handlers must be async (`async def on_message()`)
- Set `PYTHONASYNCIODEBUG=1` for debugging (enabled in main.py)

### Trigger Word System
- Case-insensitive matching: `any(word in message.content.lower() for word in TRIGGER_WORDS)`
- Current triggers include programming languages and tools (see `TRIGGER_WORDS` list in main.py)
- Bot responds in same channel, not via DM

## Deployment Architecture
- Kubernetes deployment with single replica (`replicaCount: 1`)
- No service/ingress (bot initiates outbound connections only)
- Health probes disabled (long-running process, not HTTP service)
- Resource limits: 100m-1000m CPU, 100Mi-500Mi memory
- PostgreSQL managed by CloudNativePG operator with 10Gi storage
