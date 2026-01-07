## Technical Specification (MVP): Blueprint → Runtime Business App Generator

### 1) Goal and MVP Scope

**Goal:** Build a system that generates *business web apps* from a natural-language prompt by producing a **Blueprint (JSON)** and running it through a **Runtime** that renders CRUD UI + permissions.

**MVP includes:**

* App to generate business apps via LLM (OpenRouter).
* List of generated apps with actions: **Open / Start / Stop / Delete**.
* "Generate new app" screen: **text area + submit**.
* Runtime that can render:

  * Tables (CRUD)
  * Basic relationships (lookup/select, foreign keys)
  * Role-based permissions and row-level filters
  * Navigation/menu from blueprint

**MVP excludes (explicitly out of scope):**

* Visual editor for blueprints
* Custom code execution / arbitrary plugins
* Complex workflow engines, background automations
* External integrations marketplace (can be stubbed as "coming soon")

---

### 2) High-Level Architecture

**Components**

1. **Control Plane (CP)**: manages apps, generation, lifecycle.

   * **Frontend**: Next.js (App Router) + shadcn/ui
   * **Backend**: FastAPI (REST)
   * **DB**: Postgres (recommended: Supabase Postgres)
2. **Runtime (RT)**: renders apps from blueprint.

   * **Frontend Runtime**: Next.js + **Refine** (React meta-framework for CRUD apps) ([refine.dev][1])
   * **Data Access**: Supabase (PostgREST) via Refine Supabase provider ([refine.dev][2])

**Deployment Topology (simplest MVP)**

* Single deployed web app (Next.js) hosting:

  * Control Plane UI
  * Runtime UI under `/apps/[appSlug]`
* Single FastAPI service for:

  * LLM calls (OpenRouter)
  * Blueprint validation
  * DB migrations for generated schemas
  * App lifecycle state
* One Postgres instance:

  * `control_plane` schema for metadata
  * one schema per generated app: `app_<appId>` (or `app_<slug>`)

**Lifecycle semantics**

* **Start**: sets app status = `RUNNING` (Runtime pages accessible)
* **Stop**: sets app status = `STOPPED` (Runtime pages return "App stopped")
* **Open**: navigates to Runtime URL
* **Delete**: drops app schema + deletes metadata

---

### 3) Technology Choices (MVP Constraints)

**Frontend (CP + RT)**

* Next.js (TypeScript)
* shadcn/ui + Tailwind
* Refine for runtime CRUD scaffolding and standardized auth/access control ([refine.dev][1])

**Backend**

* FastAPI + Pydantic (Blueprint schema validation + endpoints)
* SQLAlchemy (or asyncpg) for CP DB access
* Alembic (optional) for CP schema migrations; generated apps use **SQL templates** for table creation

**Auth**

* Supabase Auth (email/password) or CP-managed JWT.
* MVP recommendation: **Supabase Auth** for quickest start; Refine integrates with Supabase via `@refinedev/supabase` ([refine.dev][2])

**LLM**

* OpenRouter unified API, called from FastAPI only (never from browser). Auth via `Authorization: Bearer <key>` and OpenAI-compatible base URL `https://openrouter.ai/api/v1` ([OpenRouter][3])
* Optional headers: `HTTP-Referer`, `X-Title` ([OpenRouter][4])

---

### 4) Data Model (Control Plane)

**Schema:** `control_plane`

#### 4.1 Tables

1. `users`

* `id` (uuid, pk)
* `email` (text, unique)
* `created_at` (timestamptz)

2. `apps`

* `id` (uuid, pk)
* `owner_user_id` (uuid, fk → users.id)
* `name` (text)
* `slug` (text, unique)
* `status` (enum: `DRAFT | RUNNING | STOPPED | ERROR | DELETING`)
* `created_at` (timestamptz)
* `updated_at` (timestamptz)

3. `app_blueprints`

* `id` (uuid, pk)
* `app_id` (uuid, fk → apps.id)
* `version` (int, starts at 1)
* `blueprint_json` (jsonb)
* `blueprint_hash` (text)
* `validation_status` (enum: `VALID | INVALID`)
* `validation_errors` (jsonb, nullable)
* `created_at` (timestamptz)

4. `generation_jobs`

* `id` (uuid, pk)
* `app_id` (uuid, fk)
* `status` (enum: `QUEUED | RUNNING | SUCCEEDED | FAILED`)
* `model` (text)
* `prompt` (text)
* `llm_request` (jsonb)
* `llm_response` (jsonb)
* `error_message` (text, nullable)
* `created_at`, `updated_at` (timestamptz)

5. `app_runtime_config`

* `app_id` (uuid, pk, fk)
* `db_schema` (text) e.g. `app_<uuid>`
* `public_base_path` (text) e.g. `/apps/<slug>`
* `enabled` (bool) (mirrors RUNNING/STOPPED for routing gate)

---

### 5) Blueprint Specification (Declarative "Brain")

**Format:** JSON document validated by **JSON Schema** (stored as versioned contract in repo).
**Naming:** `BlueprintV2`.

#### 5.1 Top-level structure

```json
{
  "version": 2,
  "app": { "name": "string", "slug": "string", "description": "string", "theme": { "primaryColor": "#hex", "mode": "dark|light" } },
  "data": {
    "tables": [ /* TableSpec[] */ ],
    "relationships": [ /* RelationshipSpec[] */ ]
  },
  "security": {
    "roles": [ "Admin", "Manager", "User" ],
    "permissions": [ /* PermissionRule[] */ ],
    "rowFilters": [ /* RowFilterRule[] */ ]
  },
  "ui": {
    "navigation": [ /* NavItem[] */ ],
    "pages": [ /* PageSpec[] with blocks */ ],
    "modals": [ /* ModalSpec[] */ ]
  }
}
```

#### 5.2 TableSpec

* `name` (snake_case, unique within app)
* `primaryKey` (default `id`)
* `columns[]`:

  * `name`
  * `type` (enum: `uuid | text | int | float | bool | date | timestamptz | jsonb`)
  * `required` (bool)
  * `default` (optional)
  * `unique` (bool)
  * `indexed` (bool)
* System columns required by runtime:

  * `id uuid primary key default gen_random_uuid()`
  * `created_at timestamptz default now()`
  * `updated_at timestamptz default now()`
  * `created_by uuid nullable`

#### 5.3 RelationshipSpec (MVP)

* `type`: `many_to_one | one_to_many`
* `fromTable`, `fromColumn`
* `toTable`, `toColumn`
* `ui`: `lookupLabelColumn` (for selects)

#### 5.4 Security rules

* `permissions[]`:

  * `role`
  * `resource` (table name)
  * `actions`: `list|read|create|update|delete` booleans
* `rowFilters[]` (MVP supports simple expressions):

  * `role`
  * `resource`
  * `filter`: expression AST or restricted template

    * MVP template examples:

      * `{ "equals": ["created_by", "$user.id"] }`
      * `{ "equals": ["owner_id", "$user.id"] }`
      * `{ "in": ["team_id", "$user.team_ids"] }` (optional)

**Restriction:** No arbitrary SQL in blueprint. Only allow predefined operators: `equals`, `and`, `or`, `in`.

#### 5.5 UI Pages & Blocks

* `pages[]`:

  * `id` (unique page id)
  * `route` (URL path)
  * `title` (page title)
  * `icon` (optional icon name)
  * `layout`: `{ type: "single|split|grid|tabs", config: {} }`
  * `blocks[]`: array of UI blocks

* Available block types:
  * `TABLE` - Data grid with sorting, filtering, pagination
  * `FORM` - Dynamic form for create/edit
  * `DETAIL` - Single record display
  * `STAT-CARD` - KPI metric card
  * `CHART` - Various chart types (bar, line, pie, etc.)
  * `KANBAN` - Drag-drop board
  * `CALENDAR` - Event calendar
  * `TIMELINE` - Chronological list
  * `CHAT` - Message interface
  * `GALLERY` - Image grid
  * `TREE` - Hierarchical list

* `modals[]`:
  * `id`, `title`, `size`, `blocks[]`

---

### 6) Runtime Implementation

**Runtime behavior**

1. Load `apps/<slug>` → CP backend resolves `app_id`, status, and active blueprint version.
2. Runtime fetches `BlueprintV2` JSON.
3. Runtime dynamically constructs:

   * Page routes from `ui.pages`
   * UI blocks from each page's `blocks[]`
   * Menu items from `ui.navigation`
4. Runtime renders blocks using the block-based component system

**Auth + Access Control**

* Use `accessControlProvider.can()` to evaluate `permissions[]` for action-level gating
* For row-level security:

  * MVP enforcement should be **in DB via RLS** (preferred) or in backend query layer.
  * Implement **RLS policies** per table based on `rowFilters[]`.

**Block-based UI**

* Each block type has a dedicated renderer component
* Blocks receive data from `dataSource` configuration
* Actions are handled through the action system (navigate, openModal, etc.)

---

### 7) Blueprint → Database Provisioning

When a blueprint is accepted:

1. Compute `db_schema = app_<appIdShort>`
2. Create schema if not exists.
3. Create tables in dependency order:

   * tables without FKs first
   * then add FK constraints
4. Apply RLS policies (if Supabase):

   * enable RLS on each table
   * create policies per `rowFilters[]` + role mapping

**SQL Generation Rules**

* Column types mapped from `BlueprintV2` to Postgres types.
* Only allowed constraints: `primary key`, `unique`, `not null`, `default`, `foreign key`.
* No triggers except optional `updated_at` trigger (can be skipped; handle in UI).

**Idempotency**

* Current approach: fail if schema already exists.
* Future: support migrations between blueprint versions.

---

### 8) LLM Orchestration (OpenRouter)

**Where LLM runs:** only in FastAPI backend.

**OpenRouter integration**

* Endpoint: OpenAI-compatible `chat.completions` ([OpenRouter][6])
* Auth: `Authorization: Bearer <OPENROUTER_API_KEY>` ([OpenRouter][3])
* Base URL: `https://openrouter.ai/api/v1` ([OpenRouter][3])
* Optional headers: `HTTP-Referer`, `X-Title` ([OpenRouter][4])

**Prompting contract**

* System prompt: "Return ONLY valid JSON that conforms to BlueprintV2. No prose."
* Provide the **BlueprintV2 JSON Schema** in the prompt context (or a compact rules list).
* Add deterministic constraints:

  * Must include at least 1 table
  * Must include at least 1 role
  * Must include ui.pages with appropriate blocks for each table

**Validation loop**

1. Call LLM → get candidate JSON
2. Validate against JSON Schema (Pydantic or jsonschema)
3. If invalid: send "repair" prompt with validation errors (max 2 retries)
4. Store final blueprint + errors if failure

---

### 9) Control Plane API (FastAPI)

Base: `/api`

#### 9.1 Apps

* `GET /apps`

  * returns list: `{id, name, slug, status, created_at, updated_at}`
* `POST /apps/generate`

  * body: `{ prompt: string, model: string }`
  * returns: `{ job_id, app_id }`
* `GET /apps/{app_id}`

  * returns app details + latest blueprint metadata
* `POST /apps/{app_id}/start`

  * sets status RUNNING
* `POST /apps/{app_id}/stop`

  * sets status STOPPED
* `DELETE /apps/{app_id}`

  * marks DELETING, drops schema, removes records

#### 9.2 Blueprints

* `GET /apps/{app_id}/blueprints/latest`

  * returns blueprint JSON + version
* `GET /apps/{app_id}/blueprints/{version}`

#### 9.3 Jobs

* `GET /jobs/{job_id}`

  * returns `{status, error_message, app_id}`

---

### 10) Control Plane UI (Next.js)

#### 10.1 Pages

1. **Generate App**

* Textarea for prompt
* Model dropdown (predefined list)
* Submit → shows job progress → on success routes to App Detail

2. **Apps List**

* Table: name, slug, status, created_at
* Actions per row:

  * Open (link to `/apps/[slug]`)
  * Start / Stop (toggle)
  * Delete (confirm modal)

3. **App Detail**

* Show blueprint version, created time
* Button: Open / Start / Stop / Delete
* Show latest generation job logs (minimal)

---

### 11) Runtime Routing & Access

* Runtime entry: `/apps/[slug]`
* If app status != RUNNING → show "Stopped" page with no data calls.
* If RUNNING:

  * fetch blueprint
  * build menu/resources dynamically
  * connect to Supabase using app schema routing (see below)

**Schema targeting**

* MVP option A (recommended): Each app uses unique PostgREST endpoint schema setting (Supabase supports schema selection via client options / configuration).
* MVP option B: Prefix all tables with app id (single schema). (Simpler to implement, weaker isolation.)

---

### 12) Security Requirements (MVP)

* OpenRouter API key stored only server-side (env var).
* Strict JSON Schema validation; reject any blueprint with:

  * unknown operators
  * unknown column types
  * identifiers not matching regex: `^[a-z][a-z0-9_]{1,30}$`
* Row-level access must be enforced by DB policies (preferred with Supabase RLS), not only UI gating.
* Audit minimal:

  * `created_by` and timestamps columns on all generated tables.

---

### 13) Observability & Admin (MVP)

* Structured logs in backend for:

  * generation requests
  * blueprint validation failures
  * SQL provisioning steps
* Store `llm_request` and `llm_response` JSON in `generation_jobs` (for debugging).
* Basic health endpoint: `GET /api/health`.

---

### 14) Acceptance Criteria

1. User can submit prompt and system creates:

   * an app record
   * a valid BlueprintV2
   * DB schema + tables
2. Apps list shows new app with status RUNNING or STOPPED.
3. Open launches runtime and displays dynamic UI pages with blocks.
4. Start/Stop toggles runtime accessibility.
5. Delete removes the app and its DB schema.

---

### 15) Delivery Plan (Implementation Order)

1. Implement CP DB tables + FastAPI endpoints (apps/list/generate/start/stop/delete).
2. Implement OpenRouter LLM call + validation + retry repair.
3. Implement SQL provisioning from blueprint (create schema/tables).
4. Implement Runtime page that loads blueprint and renders block-based UI.
5. Implement CP UI (Generate + List + Detail).
6. Add basic RLS policies mapping roles → filters.

[1]: https://refine.dev/docs/?utm_source=chatgpt.com "Overview"
[2]: https://refine.dev/docs/data/packages/supabase/?utm_source=chatgpt.com "Supabase"
[3]: https://openrouter.ai/docs/api/reference/authentication?utm_source=chatgpt.com "API Authentication | OpenRouter OAuth and API Keys"
[4]: https://openrouter.ai/docs/api/reference/overview?utm_source=chatgpt.com "OpenRouter API Reference | Complete API Documentation"
[5]: https://refine.dev/docs/3.xx.xx/tutorial/getting-started/mui/generate-crud-pages/?utm_source=chatgpt.com "4. Generate CRUD pages automatically with Inferencer"
[6]: https://openrouter.ai/docs/api/api-reference/chat/send-chat-completion-request?utm_source=chatgpt.com "Create a chat completion | OpenRouter | Documentation"

