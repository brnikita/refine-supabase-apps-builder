# Blueprint V3: Full-Stack Application Generation with Amplication

## Technical Specification for Migration to V3

**Version:** 1.0  
**Date:** January 2025  
**Status:** Planning

---

## 1. Executive Summary

### 1.1 Current State (V2)

The current system generates applications with:
- ✅ **Frontend**: Dynamic UI based on Blueprint (blocks: TABLE, KANBAN, CHART, etc.)
- ✅ **Database**: Real PostgreSQL tables created via ProvisioningService
- ❌ **Backend API**: Missing — uses mock data
- ❌ **Data Layer**: No real CRUD — only stubs with console.log

### 1.2 Target State (V3)

Full-stack applications with:
- ✅ **Frontend**: Refine + dynamic blocks with real Data Provider
- ✅ **Backend**: Generated NestJS API via Amplication (open-source)
- ✅ **Database**: PostgreSQL with Prisma ORM
- ✅ **Integration**: Frontend ↔ Backend via REST API

### 1.3 Key Change

Instead of mock data on the frontend, the system will:
1. Use **Amplication** (open-source) to generate a production-ready NestJS backend
2. Connect frontend via Refine Data Provider to the generated API
3. Provide real CRUD with authentication and authorization

---

## 2. Technology Stack

### 2.1 Amplication (Open-Source Backend Generator)

**Repository:** [github.com/amplication/amplication](https://github.com/amplication/amplication)  
**License:** Apache 2.0 (open-source)

**What it is:** An open-source platform for generating production-ready backend services. Self-hosted deployment.

**Key Capabilities:**
- Generates CRUD API (REST + GraphQL) from data models
- Built-in authentication and authorization
- PostgreSQL support with Prisma ORM
- NestJS-based generated code
- Docker-ready deployment

### 2.2 Refine (Frontend Framework)

**What it is:** React meta-framework for CRUD applications

**Key Capabilities:**
- **Data Provider** — abstraction for working with any API
- Hooks: `useList`, `useOne`, `useCreate`, `useUpdate`, `useDelete`
- **Access Control Provider** — RBAC integration

---

## 3. V3 Architecture

### 3.1 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CONTROL PLANE                                      │
│                                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────────────┐   │
│  │   Frontend   │    │   Backend    │    │      LLM Service             │   │
│  │   (Next.js)  │───▶│  (FastAPI)   │───▶│   (OpenRouter)               │   │
│  │              │    │              │    │                              │   │
│  │  - Dashboard │    │  - /api/apps │    │  Generates BlueprintV3:      │   │
│  │  - Generate  │    │  - /api/jobs │    │  - Data Schema               │   │
│  └──────────────┘    └──────────────┘    │  - Backend Config            │   │
│                                          │  - Frontend UI               │   │
│                                          └──────────────┬───────────────┘   │
│                                                         │                   │
│                                                         ▼                   │
│                    ┌──────────────────────────────────────────────────┐     │
│                    │           AMPLICATION INTEGRATION                 │     │
│                    │                                                   │     │
│                    │  ┌─────────────┐  ┌─────────────────────────────┐│     │
│                    │  │ Amplication │  │  Blueprint → Amplication    ││     │
│                    │  │   Server    │  │       Converter             ││     │
│                    │  │  (self-host)│  │                             ││     │
│                    │  └─────────────┘  └─────────────────────────────┘│     │
│                    └──────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        RUNTIME LAYER                                         │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │              SINGLE RUNTIME FRONTEND (Next.js)                        │   │
│  │                                                                       │   │
│  │   /apps/task-manager  ──┐                                            │   │
│  │   /apps/crm-system    ──┼──▶  RuntimeAppV3.tsx + Refine DataProvider │   │
│  │   /apps/inventory     ──┘                                            │   │
│  │                                                                       │   │
│  │   Reads Blueprint from DB, connects to per-app backend               │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                              │                                               │
│              ┌───────────────┼───────────────┐                              │
│              ▼               ▼               ▼                              │
│  ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐            │
│  │ Backend App #1   │ │ Backend App #2   │ │ Backend App #3   │            │
│  │ (NestJS:4001)    │ │ (NestJS:4002)    │ │ (NestJS:4003)    │            │
│  │ task-manager     │ │ crm-system       │ │ inventory        │            │
│  └────────┬─────────┘ └────────┬─────────┘ └────────┬─────────┘            │
│           │                    │                    │                       │
│           └────────────────────┼────────────────────┘                       │
│                                ▼                                            │
│                    ┌──────────────────────┐                                 │
│                    │   PostgreSQL         │                                 │
│                    │   (schema per app)   │                                 │
│                    └──────────────────────┘                                 │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Data Flow

1. User submits prompt via Frontend
2. Backend sends prompt to LLM Service
3. LLM generates **BlueprintV3** (includes backend configuration)
4. **Blueprint Converter** transforms BlueprintV3 to Amplication entities format
5. **Amplication Server** (self-hosted) generates NestJS backend code
6. Generated backend is deployed and connected to PostgreSQL
7. **Runtime Frontend** connects to generated backend via Refine Data Provider

### 3.3 Frontend: Dynamic Runtime (Not Generated)

**Key decision:** Frontend is NOT generated. We use a single dynamic Runtime that renders all apps based on Blueprint.

```
┌─────────────────────────────────────────────────────────────────┐
│                     FRONTEND ARCHITECTURE                        │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              SINGLE RUNTIME (Next.js)                       │ │
│  │                                                             │ │
│  │   /apps/{slug}  →  RuntimeAppV3.tsx                        │ │
│  │                         │                                   │ │
│  │                         ▼                                   │ │
│  │              ┌─────────────────────┐                       │ │
│  │              │  Fetch Blueprint    │ ◄── from Control Plane│ │
│  │              │  from DB            │     PostgreSQL         │ │
│  │              └──────────┬──────────┘                       │ │
│  │                         │                                   │ │
│  │                         ▼                                   │ │
│  │              ┌─────────────────────┐                       │ │
│  │              │  Create DataProvider│ ◄── points to         │ │
│  │              │  for backend_url    │     generated backend │ │
│  │              └──────────┬──────────┘                       │ │
│  │                         │                                   │ │
│  │                         ▼                                   │ │
│  │              ┌─────────────────────┐                       │ │
│  │              │  Render Blocks      │                       │ │
│  │              │  (Table, Kanban...) │                       │ │
│  │              └─────────────────────┘                       │ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

**Why dynamic runtime (not generated frontend):**
- Instant updates — change Blueprint, UI updates immediately
- Single deployment — one Next.js app serves all generated apps
- Consistent UX — all apps use same block components
- Simpler architecture — no need to build/deploy frontend per app

**What changes in V3:**
- `RuntimeAppV2.tsx` → `RuntimeAppV3.tsx`
- Mock data replaced with Refine Data Provider
- Data Provider connects to generated backend API

### 3.4 Backend: Generated Code Storage

**Where generated backends are stored:**

```
/var/lib/blueprint-apps/
└── {app_id}/
    ├── src/
    │   ├── app.module.ts
    │   ├── {entity}/
    │   │   ├── {entity}.controller.ts
    │   │   ├── {entity}.service.ts
    │   │   └── dto/
    │   └── auth/
    ├── prisma/
    │   └── schema.prisma
    ├── Dockerfile
    ├── package.json
    └── metadata.json               # Deployment status, port, container ID
```

**Storage approach:**
- Generated NestJS code stored on filesystem (volume-mounted)
- Each app has isolated directory by `app_id`
- `metadata.json` tracks deployment status, assigned port, container ID

### 3.5 Backend Deployment

**How generated backends are run:**

```
┌─────────────────────────────────────────────────────────────────┐
│                    DOCKER HOST                                   │
│                                                                  │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐     │
│  │ app_abc123     │  │ app_def456     │  │ app_ghi789     │     │
│  │ (NestJS)       │  │ (NestJS)       │  │ (NestJS)       │     │
│  │ Port: 4001     │  │ Port: 4002     │  │ Port: 4003     │     │
│  └───────┬────────┘  └───────┬────────┘  └───────┬────────┘     │
│          │                   │                   │               │
│          └───────────────────┼───────────────────┘               │
│                              ▼                                   │
│                    ┌────────────────┐                            │
│                    │   PostgreSQL   │                            │
│                    │   (shared)     │                            │
│                    │                │                            │
│                    │ - app_abc123   │  ◄── schemas per app       │
│                    │ - app_def456   │                            │
│                    │ - app_ghi789   │                            │
│                    └────────────────┘                            │
└─────────────────────────────────────────────────────────────────┘
```

**Deployment approach:**
- Each generated backend runs as a Docker container
- Dynamic port allocation (4001, 4002, 4003, ...)
- Shared PostgreSQL instance with schema-per-app isolation
- Containers managed via Docker API from Control Plane

**App lifecycle:**
1. **Generate** → Amplication creates code in `/var/lib/blueprint-apps/{app_id}/backend/`
2. **Build** → Docker builds image from generated Dockerfile
3. **Deploy** → Container started with assigned port
4. **Run** → Backend accessible at `http://localhost:{port}/api`

**RuntimeConfig update:**
```json
{
  "db_schema": "app_abc123",
  "backend_url": "http://localhost:4001/api",
  "backend_port": 4001,
  "container_id": "abc123def456"
}
```

---

## 4. Blueprint V3 Schema

### 4.1 Complete Blueprint V3 Example

```json
{
  "version": 3,
  "app": {
    "name": "Task Manager",
    "slug": "task-manager",
    "description": "Kanban-style task management application"
  },
  "backend": {
    "generator": "amplication",
    "settings": {
      "generateREST": true,
      "generateSwagger": true
    },
    "auth": {
      "provider": "jwt"
    }
  },
  "data": {
    "tables": [
      {
        "name": "Project",
        "displayName": "Project",
        "columns": [
          { "name": "name", "type": "text", "required": true },
          { "name": "description", "type": "text" },
          { "name": "color", "type": "text", "default": "#6366f1" },
          { "name": "isArchived", "type": "bool", "default": false }
        ]
      },
      {
        "name": "Task",
        "displayName": "Task",
        "columns": [
          { "name": "title", "type": "text", "required": true },
          { "name": "description", "type": "text" },
          { "name": "status", "type": "text", "default": "todo" },
          { "name": "priority", "type": "text", "default": "medium" },
          { "name": "dueDate", "type": "date" }
        ]
      },
      {
        "name": "Comment",
        "displayName": "Comment",
        "columns": [
          { "name": "content", "type": "text", "required": true }
        ]
      }
    ],
    "relationships": [
      {
        "name": "project",
        "type": "many_to_one",
        "fromTable": "Task",
        "toTable": "Project"
      },
      {
        "name": "task",
        "type": "many_to_one",
        "fromTable": "Comment",
        "toTable": "Task"
      }
    ]
  },
  "security": {
    "roles": [
      { "name": "Admin", "displayName": "Administrator" },
      { "name": "User", "displayName": "User" }
    ],
    "permissions": [
      {
        "role": "Admin",
        "entity": "Project",
        "actions": { "create": true, "read": true, "update": true, "delete": true }
      },
      {
        "role": "Admin",
        "entity": "Task",
        "actions": { "create": true, "read": true, "update": true, "delete": true }
      },
      {
        "role": "Admin",
        "entity": "Comment",
        "actions": { "create": true, "read": true, "update": true, "delete": true }
      },
      {
        "role": "User",
        "entity": "Project",
        "actions": { "create": false, "read": true, "update": false, "delete": false }
      },
      {
        "role": "User",
        "entity": "Task",
        "actions": { "create": true, "read": true, "update": true, "delete": false }
      },
      {
        "role": "User",
        "entity": "Comment",
        "actions": { "create": true, "read": true, "update": true, "delete": true }
      }
    ]
  },
  "ui": {
    "navigation": [
      { "name": "projects", "label": "Projects", "icon": "folder", "route": "/projects" },
      { "name": "tasks", "label": "Tasks", "icon": "kanban", "route": "/tasks" }
    ],
    "pages": [
      {
        "id": "projects-list",
        "route": "/projects",
        "title": "Projects",
        "layout": { "type": "single" },
        "blocks": [
          {
            "id": "projects-table",
            "type": "TABLE",
            "dataSource": {
              "entity": "Project",
              "orderBy": [{ "field": "createdAt", "direction": "desc" }]
            },
            "props": {
              "columns": [
                { "field": "name", "header": "Name", "sortable": true },
                { "field": "description", "header": "Description" },
                { "field": "isArchived", "header": "Archived", "type": "boolean" }
              ],
              "allowCreate": true,
              "allowEdit": true,
              "allowDelete": true
            }
          }
        ]
      },
      {
        "id": "tasks-board",
        "route": "/tasks",
        "title": "Task Board",
        "layout": { "type": "single" },
        "blocks": [
          {
            "id": "tasks-kanban",
            "type": "KANBAN",
            "dataSource": {
              "entity": "Task",
              "include": ["project"]
            },
            "props": {
              "groupByField": "status",
              "columns": [
                { "value": "todo", "label": "To Do", "color": "#94a3b8" },
                { "value": "in_progress", "label": "In Progress", "color": "#3b82f6" },
                { "value": "done", "label": "Done", "color": "#22c55e" }
              ],
              "card": {
                "titleField": "title",
                "descriptionField": "description",
                "metaFields": ["dueDate", "priority"]
              },
              "allowDragDrop": true,
              "allowCreate": true
            }
          }
        ]
      }
    ],
    "modals": [
      {
        "id": "task-form",
        "title": "Task",
        "size": "medium",
        "blocks": [
          {
            "id": "task-form-block",
            "type": "FORM",
            "dataSource": { "entity": "Task" },
            "props": {
              "fields": [
                { "name": "title", "label": "Title", "type": "text", "required": true },
                { "name": "description", "label": "Description", "type": "textarea" },
                { "name": "status", "label": "Status", "type": "select", "options": ["todo", "in_progress", "done"] },
                { "name": "priority", "label": "Priority", "type": "select", "options": ["low", "medium", "high"] },
                { "name": "dueDate", "label": "Due Date", "type": "date" },
                { "name": "project", "label": "Project", "type": "relation" }
              ]
            }
          }
        ]
      }
    ]
  }
}
```

### 4.2 Key Schema Changes from V2

| Aspect | V2 | V3 |
|--------|----|----|
| Version | `"version": 2` | `"version": 3` |
| Backend config | None | `"backend": { ... }` section |
| Table names | snake_case (`user_tasks`) | PascalCase (`UserTask`) |
| Column names | snake_case (`due_date`) | camelCase (`dueDate`) |
| Data source | `dataSource.table` | `dataSource.entity` |
| Permissions | RLS rowFilters | Entity-action based |

### 4.3 Permissions Model Change

V2 (RLS-based):
```json
{
  "rowFilters": [
    { "role": "User", "resource": "tasks", "filter": { "equals": ["created_by", "$user.id"] } }
  ]
}
```

V3 (Entity-action based):
```json
{
  "permissions": [
    { 
      "role": "Admin", 
      "entity": "Task", 
      "actions": { "create": true, "read": true, "update": true, "delete": true }
    }
  ]
}
```

---

## 5. Key Architectural Decisions

### 5.1 Self-Hosted Amplication

**Decision:** Deploy Amplication as a self-hosted service within our infrastructure.

**Rationale:**
- Full control over code generation
- No external dependencies or API limits
- Apache 2.0 license allows commercial use
- Can be deployed via Docker Compose

### 5.2 Blueprint → Amplication Converter

**Decision:** Create a converter service that transforms BlueprintV3 to Amplication's entity format.

**Mapping:**
- Blueprint `tables` → Amplication `entities`
- Blueprint `columns` → Amplication `fields`
- Blueprint `relationships` → Amplication `relations`
- Blueprint `security.roles` → Amplication `roles`
- Blueprint `security.permissions` → Amplication `entityPermissions`

**Type Mapping:**

| Blueprint Type | Amplication DataType |
|----------------|---------------------|
| `uuid` | `Id` |
| `text` | `SingleLineText` |
| `int` | `WholeNumber` |
| `float` | `DecimalNumber` |
| `bool` | `Boolean` |
| `date` | `DateTime` |
| `jsonb` | `Json` |

### 5.3 Refine Data Provider for Amplication

**Decision:** Create a custom Refine Data Provider that communicates with Amplication-generated REST API.

**API Convention (Amplication generates):**
- `GET /api/{entity}` — list with pagination, filtering, sorting
- `GET /api/{entity}/{id}` — get one
- `POST /api/{entity}` — create
- `PATCH /api/{entity}/{id}` — update
- `DELETE /api/{entity}/{id}` — delete

### 5.4 Remove Mock Data

**Decision:** Completely remove mock data generation from RuntimeApp.

**Changes:**
- Delete `mockData` generation in `RuntimeAppV2.tsx`
- All blocks use Refine hooks (`useList`, `useCreate`, etc.)
- Data flows through Data Provider → Amplication API → PostgreSQL

### 5.5 Remove ProvisioningService for V3 Apps

**Decision:** For V3 apps, database schema is managed by Amplication/Prisma, not by our ProvisioningService.

**Rationale:**
- Amplication generates Prisma schema from entities
- Prisma handles migrations
- Avoids duplicate schema management

---

## 6. Components to Implement

### 6.1 Backend (Control Plane)

| Component | Description |
|-----------|-------------|
| `AmplicationConverter` | Converts BlueprintV3 to Amplication entities format |
| `AmplicationClient` | GraphQL client for Amplication Server API |
| `BackendGeneratorService` | Orchestrates backend generation flow |
| Updated `AppService` | Triggers backend generation after Blueprint creation |

### 6.2 Frontend (Runtime)

| Component | Description |
|-----------|-------------|
| `amplicationDataProvider.ts` | Refine Data Provider for Amplication REST API |
| `RuntimeAppV3.tsx` | Updated runtime that uses real Data Provider |
| Updated blocks | All blocks use `useList`, `useCreate`, `useUpdate`, `useDelete` |

### 6.3 Infrastructure

| Component | Description |
|-----------|-------------|
| Amplication Server | Self-hosted via Docker Compose |
| Per-app NestJS containers | Generated backends deployed as containers |

---

## 7. Migration Tasks

### 7.1 Infrastructure Setup

- [ ] Deploy self-hosted Amplication using Docker Compose
- [ ] Configure Amplication PostgreSQL database
- [ ] Set up Amplication authentication

### 7.2 Backend Development

- [ ] Create `AmplicationConverter` service
- [ ] Create `AmplicationClient` service (GraphQL)
- [ ] Create `BackendGeneratorService`
- [ ] Update `AppService` to trigger backend generation
- [ ] Add BlueprintV3 Pydantic schemas with `backend` section

### 7.3 Frontend Development

- [ ] Create `amplicationDataProvider.ts`
- [ ] Create `RuntimeAppV3.tsx` with Refine integration
- [ ] Update `TableBlock` to use `useList`
- [ ] Update `FormBlock` to use `useCreate`/`useUpdate`
- [ ] Update `KanbanBlock` to use real CRUD
- [ ] Update remaining blocks
- [ ] Remove all mock data generation

### 7.4 LLM Prompt Update

- [ ] Update system prompt to generate BlueprintV3 with `backend` section
- [ ] Add PascalCase entity naming requirement
- [ ] Add entity-action permissions format

### 7.5 Schema Updates

- [ ] Add `backend` section to Blueprint Pydantic models
- [ ] Add `backend` section to Blueprint TypeScript types
- [ ] Create V2 → V3 migration utility (for existing apps)

---

## 8. Risks and Mitigation

| Risk | Mitigation |
|------|------------|
| Amplication API changes | Pin Amplication version in Docker |
| Generated code doesn't match expectations | Validate generated entities before deployment |
| Performance overhead from code generation | Cache generated code, generate once per Blueprint change |

---

## 9. Success Criteria

- [ ] Generated apps have working CRUD operations (no mock data)
- [ ] Authentication works end-to-end
- [ ] All existing block types work with real data
- [ ] New apps are generated with both frontend and backend
- [ ] Generated backends are accessible via REST API
