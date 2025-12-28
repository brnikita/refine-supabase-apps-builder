# Dynamic UI Rendering System - Technical Specification

## Problem Statement

The current system generates all apps with identical table-based CRUD interfaces regardless of what the user requests. When a user asks for a "kanban board", "chat application", or "calendar app", they receive the same generic table UI with different column names.

**Goal**: Enable the system to generate visually and functionally unique applications that match the user's intent, without relying on predefined templates.

---

## Solution Overview

### Core Principle: **Declarative UI Blocks with Component Composition**

Instead of hardcoded UI patterns, the system uses:
1. **UI Blocks** - Atomic, reusable visual components (table, kanban, chart, form, etc.)
2. **Layout System** - Flexible arrangement of blocks on pages
3. **Component Registry** - Runtime mapping of block types to React components
4. **LLM-Driven Generation** - AI determines which blocks and layouts best serve the user's request

---

## Architecture

### High-Level Flow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   User Prompt   │────▶│   LLM Engine    │────▶│   Blueprint     │
│                 │     │                 │     │   (JSON)        │
│ "Create a       │     │ Analyzes intent │     │                 │
│  kanban board   │     │ Selects blocks  │     │ - Data schema   │
│  for tasks"     │     │ Designs layout  │     │ - UI pages      │
│                 │     │                 │     │ - Block configs │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                                                         ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Rendered App  │◀────│  Block Renderer │◀────│  Runtime Engine │
│                 │     │                 │     │                 │
│ Kanban board    │     │ Maps block type │     │ Loads blueprint │
│ with columns,   │     │ to component    │     │ Builds routes   │
│ drag-drop, etc  │     │ Passes props    │     │ Fetches data    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

---

## Blueprint Schema v2

### Top-Level Structure

```json
{
  "version": 2,
  "app": {
    "name": "Task Manager",
    "slug": "task-manager",
    "description": "Kanban-style task management",
    "theme": {
      "primaryColor": "#6366f1",
      "mode": "dark"
    }
  },
  "data": {
    "tables": [...],
    "relationships": [...]
  },
  "security": {
    "roles": [...],
    "permissions": [...],
    "rowFilters": [...]
  },
  "ui": {
    "navigation": [...],
    "pages": [...],
    "modals": [...],
    "globalActions": [...]
  }
}
```

### Page Definition

```json
{
  "id": "tasks-board",
  "route": "/tasks",
  "title": "Task Board",
  "icon": "layout-kanban",
  "layout": {
    "type": "single",  // single | split | grid | tabs
    "config": {}
  },
  "blocks": [
    {
      "id": "main-kanban",
      "type": "kanban",
      "dataSource": {
        "table": "tasks",
        "filters": [],
        "orderBy": [{ "field": "position", "direction": "asc" }]
      },
      "props": {
        "groupByField": "status",
        "columns": [
          { "value": "backlog", "label": "Backlog", "color": "#94a3b8" },
          { "value": "todo", "label": "To Do", "color": "#3b82f6" },
          { "value": "in_progress", "label": "In Progress", "color": "#f59e0b" },
          { "value": "done", "label": "Done", "color": "#22c55e" }
        ],
        "card": {
          "titleField": "title",
          "descriptionField": "description",
          "metaFields": ["assignee_id", "due_date", "priority"],
          "colorField": "priority"
        },
        "allowDragDrop": true,
        "allowCreate": true,
        "allowEdit": true
      },
      "actions": [
        { "trigger": "cardClick", "action": "openModal", "modal": "task-detail" },
        { "trigger": "cardMove", "action": "updateRecord", "field": "status" }
      ]
    }
  ]
}
```

---

## Block Types Catalog

### Core Blocks (Must Have)

| Block Type | Description | Use Cases |
|------------|-------------|-----------|
| `table` | Data grid with sorting, filtering, pagination | Lists, reports, admin panels |
| `form` | Dynamic form with validation | Create/edit records |
| `detail` | Single record display | View record details |
| `stat-card` | Metric display with optional trend | Dashboards, KPIs |
| `chart` | Various chart types (bar, line, pie, etc.) | Analytics, reports |

### Layout Blocks

| Block Type | Description | Use Cases |
|------------|-------------|-----------|
| `container` | Groups other blocks | Sections, cards |
| `tabs` | Tabbed content | Multi-view pages |
| `split-view` | Side-by-side panels | Master-detail |
| `accordion` | Collapsible sections | FAQs, settings |

### Specialized Blocks

| Block Type | Description | Use Cases |
|------------|-------------|-----------|
| `kanban` | Drag-drop columns | Task boards, pipelines |
| `calendar` | Month/week/day views | Events, scheduling |
| `timeline` | Chronological list | Activity logs, history |
| `chat` | Message thread | Conversations, comments |
| `gallery` | Image/card grid | Media, products |
| `map` | Geographic display | Locations, routes |
| `tree` | Hierarchical list | Categories, org charts |
| `markdown` | Rich text display | Documentation, notes |
| `embed` | External content | Videos, widgets |
| `file-list` | File management | Documents, attachments |

### Interactive Blocks

| Block Type | Description | Use Cases |
|------------|-------------|-----------|
| `button` | Action trigger | Navigation, actions |
| `search` | Search input | Global search |
| `filter-bar` | Filter controls | Data filtering |
| `toolbar` | Action buttons group | Bulk actions |

---

## Block Specification

### Common Block Properties

```typescript
interface BlockSpec {
  id: string;                    // Unique identifier
  type: string;                  // Block type from registry
  
  // Data binding
  dataSource?: {
    table: string;               // Source table
    filters?: FilterSpec[];      // Static filters
    orderBy?: OrderSpec[];       // Default sorting
    limit?: number;              // Record limit
    include?: string[];          // Related data to include
  };
  
  // Visual configuration
  props: Record<string, any>;    // Type-specific properties
  
  // Layout
  gridArea?: string;             // CSS grid placement
  className?: string;            // Custom CSS classes
  
  // Behavior
  actions?: ActionSpec[];        // Event handlers
  visibility?: VisibilityRule;   // Conditional display
  
  // Nested blocks (for containers)
  children?: BlockSpec[];
}
```

### Action Specification

```typescript
interface ActionSpec {
  trigger: string;               // Event name (click, submit, change, etc.)
  action: string;                // Action type
  config: Record<string, any>;   // Action-specific config
  condition?: string;            // Optional condition expression
}

// Action Types:
// - navigate: Go to route
// - openModal: Show modal dialog
// - closeModal: Close modal
// - createRecord: Insert new record
// - updateRecord: Update existing record
// - deleteRecord: Remove record
// - apiCall: Custom API request
// - showNotification: Display message
// - downloadFile: Trigger download
// - copyToClipboard: Copy text
// - setVariable: Set page variable
// - refresh: Reload data
```

---

## Layout System

### Layout Types

#### 1. Single (Default)
Full-width content area with stacked blocks.

```json
{
  "type": "single",
  "config": {
    "maxWidth": "1200px",
    "padding": "24px"
  }
}
```

#### 2. Split
Two-panel layout (master-detail pattern).

```json
{
  "type": "split",
  "config": {
    "direction": "horizontal",  // horizontal | vertical
    "sizes": [30, 70],          // Percentage widths
    "resizable": true
  }
}
```

#### 3. Grid
CSS Grid-based layout for dashboards.

```json
{
  "type": "grid",
  "config": {
    "columns": 4,
    "rows": "auto",
    "gap": "16px"
  }
}
```

#### 4. Tabs
Tabbed interface for multiple views.

```json
{
  "type": "tabs",
  "config": {
    "position": "top",          // top | left | bottom
    "tabs": [
      { "id": "overview", "label": "Overview", "icon": "home" },
      { "id": "details", "label": "Details", "icon": "list" }
    ]
  }
}
```

---

## Component Registry

### Architecture

```typescript
// Component Registry Pattern
const componentRegistry: Record<string, React.ComponentType<any>> = {
  // Core
  'table': DataTable,
  'form': DynamicForm,
  'detail': DetailView,
  'stat-card': StatCard,
  'chart': ChartWidget,
  
  // Layout
  'container': Container,
  'tabs': TabsContainer,
  'split-view': SplitView,
  
  // Specialized
  'kanban': KanbanBoard,
  'calendar': CalendarView,
  'timeline': TimelineView,
  'chat': ChatInterface,
  'gallery': GalleryGrid,
  
  // Interactive
  'button': ActionButton,
  'search': SearchInput,
  'filter-bar': FilterBar,
};

// Block Renderer
function BlockRenderer({ block, context }: Props) {
  const Component = componentRegistry[block.type];
  
  if (!Component) {
    return <UnknownBlock type={block.type} />;
  }
  
  return (
    <BlockDataProvider 
      dataSource={block.dataSource}
      context={context}
    >
      <Component 
        {...block.props}
        actions={block.actions}
        blockId={block.id}
      />
    </BlockDataProvider>
  );
}
```

### Block Component Contract

Each block component must implement:

```typescript
interface BlockComponentProps<T = any> {
  // Data (injected by BlockDataProvider)
  data?: T[];
  loading?: boolean;
  error?: Error;
  
  // CRUD operations (injected)
  onCreate?: (data: Partial<T>) => Promise<T>;
  onUpdate?: (id: string, data: Partial<T>) => Promise<T>;
  onDelete?: (id: string) => Promise<void>;
  onRefresh?: () => void;
  
  // Block-specific props
  [key: string]: any;
  
  // Actions
  actions?: ActionSpec[];
  
  // Context
  blockId: string;
}
```

---

## Data Provider Layer

### BlockDataProvider

Handles data fetching, caching, and mutations for each block.

```typescript
interface DataProviderConfig {
  table: string;
  filters?: FilterSpec[];
  orderBy?: OrderSpec[];
  limit?: number;
  include?: string[];           // Relations to include
  realtime?: boolean;           // Enable realtime subscriptions
}

function BlockDataProvider({ 
  dataSource, 
  context, 
  children 
}: Props) {
  const { data, loading, error, refetch } = useQuery(dataSource);
  const { create, update, remove } = useMutations(dataSource.table);
  
  return (
    <BlockContext.Provider value={{
      data,
      loading,
      error,
      onCreate: create,
      onUpdate: update,
      onDelete: remove,
      onRefresh: refetch,
    }}>
      {children}
    </BlockContext.Provider>
  );
}
```

---

## Template Expressions

Props support dynamic values via template expressions:

### Syntax

| Expression | Description | Example |
|------------|-------------|---------|
| `{{field}}` | Current record field | `{{title}}` |
| `{{$user.id}}` | Current user property | `{{$user.email}}` |
| `{{$page.variable}}` | Page-level variable | `{{$page.selectedId}}` |
| `{{$route.param}}` | URL parameter | `{{$route.id}}` |
| `{{$now}}` | Current timestamp | `{{$now}}` |

### Formatters

```
{{field | format}}

Formatters:
- date: Format as date
- datetime: Format as datetime
- currency: Format as currency
- number: Format with decimals
- uppercase: Convert to uppercase
- lowercase: Convert to lowercase
- truncate:N: Truncate to N chars
- default:value: Default if empty
```

### Expressions in Filters

```json
{
  "filters": [
    { "field": "owner_id", "operator": "eq", "value": "{{$user.id}}" },
    { "field": "due_date", "operator": "gte", "value": "{{$now}}" }
  ]
}
```

---

## LLM Generation Strategy

### System Prompt Structure

```
You are a UI architect generating application blueprints.

AVAILABLE BLOCK TYPES:
[List of all block types with descriptions and use cases]

BLOCK SELECTION GUIDELINES:
1. Analyze the user's request to understand the core functionality
2. Select blocks that best represent the data and workflows
3. Consider user experience - choose intuitive layouts
4. Combine blocks to create rich interfaces

EXAMPLES:
- "task management" → kanban for tasks, table for projects, stat-cards for dashboard
- "CRM" → table for contacts, timeline for activities, chart for pipeline
- "scheduling app" → calendar for events, form for booking, table for resources
- "inventory system" → table for products, stat-cards for stock levels, chart for trends
- "social feed" → timeline for posts, chat for comments, gallery for media

LAYOUT GUIDELINES:
- Dashboards: Use grid layout with stat-cards and charts
- Data-heavy apps: Use table as primary, detail view for records
- Workflow apps: Use kanban or timeline as primary
- Scheduling apps: Use calendar as primary
- Collaborative apps: Include chat or comments blocks

OUTPUT FORMAT:
Generate complete BlueprintV2 JSON with appropriate blocks for each page.
```

### Generation Process

1. **Intent Analysis**: LLM identifies app type and core features
2. **Data Modeling**: Generate tables and relationships
3. **Page Planning**: Determine pages needed and their purposes
4. **Block Selection**: Choose appropriate blocks for each page
5. **Layout Design**: Arrange blocks with suitable layouts
6. **Action Wiring**: Connect blocks with actions and navigation

---

## Example Generated Blueprints

### Example 1: Kanban Task Board

User prompt: *"Create a kanban board for managing tasks with priorities and assignees"*

```json
{
  "version": 2,
  "app": {
    "name": "Task Board",
    "slug": "task-board",
    "description": "Kanban-style task management"
  },
  "data": {
    "tables": [
      {
        "name": "tasks",
        "columns": [
          { "name": "title", "type": "text", "required": true },
          { "name": "description", "type": "text" },
          { "name": "status", "type": "text", "default": "backlog" },
          { "name": "priority", "type": "text", "default": "medium" },
          { "name": "assignee_id", "type": "uuid" },
          { "name": "due_date", "type": "date" },
          { "name": "position", "type": "int", "default": 0 }
        ]
      },
      {
        "name": "users",
        "columns": [
          { "name": "name", "type": "text", "required": true },
          { "name": "email", "type": "text", "required": true },
          { "name": "avatar_url", "type": "text" }
        ]
      }
    ],
    "relationships": [
      {
        "type": "many_to_one",
        "fromTable": "tasks",
        "fromColumn": "assignee_id",
        "toTable": "users",
        "toColumn": "id",
        "lookupLabelColumn": "name"
      }
    ]
  },
  "ui": {
    "navigation": [
      { "name": "board", "label": "Board", "icon": "layout-kanban", "route": "/" },
      { "name": "list", "label": "List View", "icon": "list", "route": "/list" },
      { "name": "team", "label": "Team", "icon": "users", "route": "/team" }
    ],
    "pages": [
      {
        "id": "board",
        "route": "/",
        "title": "Task Board",
        "layout": { "type": "single" },
        "blocks": [
          {
            "id": "task-kanban",
            "type": "kanban",
            "dataSource": {
              "table": "tasks",
              "include": ["assignee"],
              "orderBy": [{ "field": "position", "direction": "asc" }]
            },
            "props": {
              "groupByField": "status",
              "columns": [
                { "value": "backlog", "label": "Backlog", "color": "#94a3b8" },
                { "value": "todo", "label": "To Do", "color": "#3b82f6" },
                { "value": "in_progress", "label": "In Progress", "color": "#f59e0b" },
                { "value": "review", "label": "Review", "color": "#8b5cf6" },
                { "value": "done", "label": "Done", "color": "#22c55e" }
              ],
              "card": {
                "titleField": "title",
                "descriptionField": "description",
                "metaFields": ["assignee_id", "due_date"],
                "badgeField": "priority",
                "badgeColors": {
                  "high": "#ef4444",
                  "medium": "#f59e0b",
                  "low": "#22c55e"
                }
              },
              "allowDragDrop": true,
              "allowCreate": true
            },
            "actions": [
              { "trigger": "cardClick", "action": "openModal", "config": { "modal": "task-detail" } },
              { "trigger": "cardMove", "action": "updateRecord", "config": { "field": "status" } },
              { "trigger": "createClick", "action": "openModal", "config": { "modal": "task-create" } }
            ]
          }
        ]
      },
      {
        "id": "list",
        "route": "/list",
        "title": "All Tasks",
        "layout": { "type": "single" },
        "blocks": [
          {
            "id": "task-table",
            "type": "table",
            "dataSource": {
              "table": "tasks",
              "include": ["assignee"]
            },
            "props": {
              "columns": [
                { "field": "title", "label": "Title", "sortable": true },
                { "field": "status", "label": "Status", "type": "badge" },
                { "field": "priority", "label": "Priority", "type": "badge" },
                { "field": "assignee.name", "label": "Assignee" },
                { "field": "due_date", "label": "Due Date", "type": "date" }
              ],
              "allowSearch": true,
              "allowFilter": true,
              "allowSort": true,
              "rowActions": ["edit", "delete"]
            }
          }
        ]
      }
    ],
    "modals": [
      {
        "id": "task-detail",
        "title": "Task Details",
        "size": "medium",
        "blocks": [
          {
            "id": "task-form",
            "type": "form",
            "dataSource": { "table": "tasks" },
            "props": {
              "mode": "edit",
              "fields": [
                { "name": "title", "label": "Title", "type": "text", "required": true },
                { "name": "description", "label": "Description", "type": "textarea" },
                { "name": "status", "label": "Status", "type": "select", "options": ["backlog", "todo", "in_progress", "review", "done"] },
                { "name": "priority", "label": "Priority", "type": "select", "options": ["low", "medium", "high"] },
                { "name": "assignee_id", "label": "Assignee", "type": "relation", "table": "users" },
                { "name": "due_date", "label": "Due Date", "type": "date" }
              ]
            }
          }
        ]
      }
    ]
  }
}
```

### Example 2: Team Chat Application

User prompt: *"Build a team chat app with channels and direct messages"*

```json
{
  "version": 2,
  "app": {
    "name": "Team Chat",
    "slug": "team-chat",
    "description": "Real-time team communication"
  },
  "data": {
    "tables": [
      {
        "name": "channels",
        "columns": [
          { "name": "name", "type": "text", "required": true },
          { "name": "description", "type": "text" },
          { "name": "is_private", "type": "bool", "default": false }
        ]
      },
      {
        "name": "messages",
        "columns": [
          { "name": "content", "type": "text", "required": true },
          { "name": "channel_id", "type": "uuid" },
          { "name": "sender_id", "type": "uuid" },
          { "name": "reply_to_id", "type": "uuid" }
        ]
      },
      {
        "name": "users",
        "columns": [
          { "name": "name", "type": "text", "required": true },
          { "name": "avatar_url", "type": "text" },
          { "name": "status", "type": "text", "default": "offline" }
        ]
      }
    ]
  },
  "ui": {
    "pages": [
      {
        "id": "chat",
        "route": "/",
        "title": "Chat",
        "layout": {
          "type": "split",
          "config": { "sizes": [25, 75], "direction": "horizontal" }
        },
        "blocks": [
          {
            "id": "channel-list",
            "type": "tree",
            "dataSource": { "table": "channels" },
            "props": {
              "titleField": "name",
              "iconField": "is_private",
              "icons": { "true": "lock", "false": "hash" },
              "showUserStatus": true
            },
            "actions": [
              { "trigger": "itemClick", "action": "setVariable", "config": { "name": "selectedChannel", "value": "{{id}}" } }
            ]
          },
          {
            "id": "message-thread",
            "type": "chat",
            "dataSource": {
              "table": "messages",
              "filters": [{ "field": "channel_id", "operator": "eq", "value": "{{$page.selectedChannel}}" }],
              "include": ["sender"],
              "orderBy": [{ "field": "created_at", "direction": "asc" }]
            },
            "props": {
              "messageField": "content",
              "senderField": "sender",
              "senderNameField": "sender.name",
              "senderAvatarField": "sender.avatar_url",
              "timestampField": "created_at",
              "allowReply": true,
              "allowReactions": true,
              "allowAttachments": true,
              "realtime": true
            }
          }
        ]
      }
    ]
  }
}
```

### Example 3: Event Calendar

User prompt: *"Create a calendar app for scheduling meetings and events"*

```json
{
  "version": 2,
  "app": {
    "name": "Event Calendar",
    "slug": "event-calendar",
    "description": "Meeting and event scheduling"
  },
  "data": {
    "tables": [
      {
        "name": "events",
        "columns": [
          { "name": "title", "type": "text", "required": true },
          { "name": "description", "type": "text" },
          { "name": "start_time", "type": "timestamptz", "required": true },
          { "name": "end_time", "type": "timestamptz", "required": true },
          { "name": "location", "type": "text" },
          { "name": "category", "type": "text" },
          { "name": "is_recurring", "type": "bool", "default": false },
          { "name": "recurrence_rule", "type": "text" }
        ]
      },
      {
        "name": "attendees",
        "columns": [
          { "name": "event_id", "type": "uuid" },
          { "name": "user_id", "type": "uuid" },
          { "name": "status", "type": "text", "default": "pending" }
        ]
      }
    ]
  },
  "ui": {
    "navigation": [
      { "name": "calendar", "label": "Calendar", "icon": "calendar", "route": "/" },
      { "name": "upcoming", "label": "Upcoming", "icon": "clock", "route": "/upcoming" }
    ],
    "pages": [
      {
        "id": "calendar",
        "route": "/",
        "title": "Calendar",
        "layout": { "type": "single" },
        "blocks": [
          {
            "id": "event-calendar",
            "type": "calendar",
            "dataSource": { "table": "events" },
            "props": {
              "startField": "start_time",
              "endField": "end_time",
              "titleField": "title",
              "colorField": "category",
              "colors": {
                "meeting": "#3b82f6",
                "deadline": "#ef4444",
                "reminder": "#f59e0b",
                "personal": "#22c55e"
              },
              "views": ["month", "week", "day", "agenda"],
              "defaultView": "week",
              "allowCreate": true,
              "allowDrag": true,
              "allowResize": true
            },
            "actions": [
              { "trigger": "eventClick", "action": "openModal", "config": { "modal": "event-detail" } },
              { "trigger": "slotClick", "action": "openModal", "config": { "modal": "event-create", "data": { "start_time": "{{start}}", "end_time": "{{end}}" } } },
              { "trigger": "eventDrop", "action": "updateRecord", "config": { "fields": ["start_time", "end_time"] } }
            ]
          }
        ]
      },
      {
        "id": "upcoming",
        "route": "/upcoming",
        "title": "Upcoming Events",
        "layout": { "type": "single" },
        "blocks": [
          {
            "id": "upcoming-timeline",
            "type": "timeline",
            "dataSource": {
              "table": "events",
              "filters": [{ "field": "start_time", "operator": "gte", "value": "{{$now}}" }],
              "orderBy": [{ "field": "start_time", "direction": "asc" }],
              "limit": 20
            },
            "props": {
              "dateField": "start_time",
              "titleField": "title",
              "descriptionField": "description",
              "groupBy": "day",
              "showTime": true
            }
          }
        ]
      }
    ]
  }
}
```

---

## Implementation Phases

### Phase 1: Core Infrastructure (Week 1-2)
- [ ] Update Blueprint schema to v2 with pages/blocks
- [ ] Implement BlockRenderer component
- [ ] Create component registry pattern
- [ ] Build BlockDataProvider for data fetching
- [ ] Implement basic layout system (single, grid)

### Phase 2: Essential Blocks (Week 2-3)
- [ ] `table` - Data grid with CRUD
- [ ] `form` - Dynamic form generation
- [ ] `detail` - Record detail view
- [ ] `stat-card` - Metric display
- [ ] `chart` - Basic charts (bar, line, pie)
- [ ] `container` - Block grouping

### Phase 3: Specialized Blocks (Week 3-4)
- [ ] `kanban` - Drag-drop board
- [ ] `calendar` - Event calendar
- [ ] `timeline` - Chronological list
- [ ] `chat` - Message interface
- [ ] `gallery` - Grid display

### Phase 4: Advanced Features (Week 4-5)
- [ ] Template expressions engine
- [ ] Action system (navigation, modals, API calls)
- [ ] Split and tabs layouts
- [ ] Modal system
- [ ] Real-time data subscriptions

### Phase 5: LLM Integration (Week 5-6)
- [ ] Update LLM prompt with block catalog
- [ ] Add block selection guidelines
- [ ] Test with various app types
- [ ] Fine-tune generation quality

---

## Success Criteria

1. **Variety**: Same prompt type generates visually different apps based on context
2. **Accuracy**: Generated UI matches user intent (kanban for tasks, calendar for events, etc.)
3. **Completeness**: All necessary CRUD operations work for each block type
4. **Usability**: Generated apps are immediately usable without manual fixes
5. **Extensibility**: New block types can be added without core changes

---

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| LLM generates invalid block configs | Strict JSON schema validation + repair prompts |
| Block type not suitable for data | LLM guidelines + fallback to table |
| Complex layouts break on mobile | Responsive design in all blocks |
| Performance with many blocks | Lazy loading + virtualization |
| Data provider complexity | Standardized interface + caching |

---

## Appendix: Block Props Reference

### Table Block
```typescript
interface TableProps {
  columns: ColumnDef[];
  allowSearch?: boolean;
  allowFilter?: boolean;
  allowSort?: boolean;
  allowSelect?: boolean;
  allowExport?: boolean;
  pagination?: { pageSize: number };
  rowActions?: ('view' | 'edit' | 'delete' | ActionSpec)[];
  emptyMessage?: string;
}
```

### Kanban Block
```typescript
interface KanbanProps {
  groupByField: string;
  columns: { value: string; label: string; color?: string; limit?: number }[];
  card: {
    titleField: string;
    descriptionField?: string;
    metaFields?: string[];
    badgeField?: string;
    badgeColors?: Record<string, string>;
    avatarField?: string;
  };
  allowDragDrop?: boolean;
  allowCreate?: boolean;
  allowCollapse?: boolean;
}
```

### Calendar Block
```typescript
interface CalendarProps {
  startField: string;
  endField: string;
  titleField: string;
  colorField?: string;
  colors?: Record<string, string>;
  views?: ('month' | 'week' | 'day' | 'agenda')[];
  defaultView?: string;
  allowCreate?: boolean;
  allowDrag?: boolean;
  allowResize?: boolean;
  minTime?: string;
  maxTime?: string;
}
```

### Chat Block
```typescript
interface ChatProps {
  messageField: string;
  senderField: string;
  senderNameField: string;
  senderAvatarField?: string;
  timestampField: string;
  allowReply?: boolean;
  allowReactions?: boolean;
  allowAttachments?: boolean;
  allowEdit?: boolean;
  allowDelete?: boolean;
  realtime?: boolean;
}
```

### Chart Block
```typescript
interface ChartProps {
  chartType: 'bar' | 'line' | 'pie' | 'donut' | 'area' | 'scatter';
  xField?: string;
  yField?: string;
  groupField?: string;
  aggregation?: 'count' | 'sum' | 'avg' | 'min' | 'max';
  colors?: string[];
  showLegend?: boolean;
  showGrid?: boolean;
  animate?: boolean;
}
```

