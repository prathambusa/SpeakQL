# SpeakQL

SpeakQL lets non-technical users query any SQL database in plain English. Type a question, and SpeakQL automatically retrieves the relevant schema context, generates a safe `SELECT` query with Claude, executes it, and renders the results as a sortable, filterable table — no SQL knowledge required.

---

## Architecture

```
Browser
  │
  │  POST /query {"question": "...", "db_alias": "..."}
  ▼
┌──────────────────────────────────────────────────────┐
│                  FastAPI Backend                      │
│                                                      │
│  Step 1 — RAG Retrieval                              │
│    ┌─────────────┐    embed question                  │
│    │   Chroma    │◄────────────────── question text   │
│    │  (per-DB    │  similarity search                 │
│    │  collection)│──────────────────► top-K tables    │
│    └─────────────┘                                   │
│                                                      │
│  Step 2 — SQL Generation                             │
│    ┌─────────────┐    schema + question               │
│    │   Claude    │◄────────────────── (LangChain)     │
│    │  (or GPT-4o)│──────────────────► raw SQL         │
│    └─────────────┘    + reasoning trace               │
│                                                      │
│  Step 3 — Safe Execution                             │
│    sqlglot AST check → keyword blocklist → LIMIT cap │
│    ┌─────────────┐                                   │
│    │ PostgreSQL  │◄── SQLAlchemy async engine         │
│    │  (or SQLite)│──────────────────► rows            │
│    └─────────────┘                                   │
│                                                      │
│  Step 4 — Response                                   │
│    Format SQL (sqlglot) → JSON → browser             │
└──────────────────────────────────────────────────────┘
  │
  ▼
┌──────────────────────────────┐
│   React + Vite + Tailwind    │
│   QueryBar · ResultsTable    │
│   SQLViewer · StatusBar      │
└──────────────────────────────┘
```

---

## Quickstart with Docker Compose

```bash
# 1. Clone the repo
git clone https://github.com/yourorg/speakql.git
cd speakql

# 2. Copy environment template and fill in your keys
cp .env.example .env
# Edit .env — at minimum set ANTHROPIC_API_KEY and OPENAI_API_KEY

# 3. Start everything (Postgres + Northwind seed, Chroma, backend, frontend)
docker compose up --build

# 4. Open the app
open http://localhost:5173
```

The backend auto-indexes the Northwind schema on first startup. Try asking:

- "Which products cost more than $30?"
- "How many orders were shipped to Germany?"
- "Who are the top 5 customers by total freight paid?"

---

## Connecting Your Own Database

1. **Add a DB alias to `.env`:**

   ```env
   DB_ALIASES=default,mydb
   DB_MYDB_URL=postgresql+asyncpg://readonly_user:pass@host:5432/mydb
   ```

2. **Re-index the schema** (run once after connecting):

   ```bash
   curl -X POST "http://localhost:8000/refresh-schema?db_alias=mydb"
   ```

3. **Query it** by passing `db_alias` in the UI DB field (or via API):

   ```bash
   curl -X POST http://localhost:8000/query \
     -H 'Content-Type: application/json' \
     -d '{"question": "How many users signed up last week?", "db_alias": "mydb"}'
   ```

> **Production tip:** create a read-only Postgres role first — see `db/seed/create_readonly_role.sql`.

---

## Adding a New LLM Provider

1. Add your provider's LangChain chat class in `backend/pipeline/agent.py` inside `_build_llm()`:

   ```python
   elif settings.llm_provider == "my_provider":
       from langchain_myprovider import ChatMyProvider
       return ChatMyProvider(model="...", api_key=settings.my_api_key, temperature=0)
   ```

2. Add the SDK to `backend/requirements.txt` and pin the version.

3. Set `LLM_PROVIDER=my_provider` in `.env`.

---

## Running Tests

```bash
cd backend
pip install -r requirements.txt
pytest ../tests/ -v
```

Tests use an in-memory SQLite database — no external services required.

---

## API Reference

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/query` | Run the four-step pipeline |
| `GET`  | `/schema` | Return all indexed tables |
| `POST` | `/refresh-schema` | Re-introspect DB and re-index Chroma |
| `GET`  | `/health` | Liveness check |

**`POST /query` request:**
```json
{ "question": "Which customers are in Germany?", "db_alias": "default" }
```

**`POST /query` response:**
```json
{
  "question": "Which customers are in Germany?",
  "sql": "SELECT customer_id, company_name FROM customers WHERE country = 'Germany'",
  "execution_time_ms": 4.2,
  "row_count": 11,
  "columns": ["customer_id", "company_name"],
  "rows": [["ALFKI", "Alfreds Futterkiste"], ...],
  "clarify": false,
  "clarify_message": null,
  "error": null,
  "reasoning_trace": "The question asks for customers by country..."
}
```

---

## Safety Guardrails

| Layer | What it does |
|-------|-------------|
| Input sanitization | Questions stripped and capped at 500 chars |
| RAG scope | Only retrieved table schemas are in the prompt — never the full DB |
| LLM prompt rules | Model instructed to use SELECT only; clarify instead of hallucinate |
| Regex blocklist | `DROP\|DELETE\|UPDATE\|INSERT\|TRUNCATE\|ALTER\|CREATE\|EXEC` rejected before DB |
| AST validation | `sqlglot.parse` confirms top-level statement is `SELECT` |
| Read-only engine | Connect as a read-only Postgres role in production |
| Row cap | `LIMIT 1000` auto-injected if not present |
| Query timeout | 30-second hard timeout via `asyncio.wait_for` |
| Rate limiting | 10 requests/minute per IP (`slowapi`) |

---

## Known Limitations

- **Embedding provider**: only OpenAI (`text-embedding-3-small`) is currently supported for schema embedding. Voyage AI can be added via `chromadb`'s embedding functions.
- **Schema drift**: if you change your DB schema, run `POST /refresh-schema` to re-index.
- **Complex queries**: very large schemas (100+ tables) may exceed context limits — `TOP_K_TABLES` controls retrieval scope.
- **SQLite read-only mode**: the dev SQLite DB is not enforced as read-only at the driver level; the AST + blocklist guards still apply.
- **No auth**: the API has no authentication layer — add a reverse proxy or API key middleware before exposing publicly.
