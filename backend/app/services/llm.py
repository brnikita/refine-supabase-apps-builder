import httpx
import json
import logging
from typing import Dict, Any, Optional, Tuple

from app.config import settings

logger = logging.getLogger(__name__)

# V3 Blueprint System Prompt
BLUEPRINT_V3_SYSTEM_PROMPT = """You are a full-stack application architect generating BlueprintV3 JSON documents. Generate a valid BlueprintV3 JSON for a business web application based on the user's description.

CRITICAL RULES:
1. Return ONLY valid JSON that conforms to BlueprintV3 schema. No prose, no markdown, no explanations.
2. The JSON must be parseable directly.
3. Choose appropriate UI blocks based on the application type - DO NOT default to tables for everything.
4. Use PascalCase for entity names (e.g., "Task", "Project", "UserComment")
5. Use camelCase for field names (e.g., "dueDate", "isCompleted", "createdAt")

BlueprintV3 Schema:
{
  "version": 3,
  "app": {
    "name": "string",
    "slug": "string (lowercase, hyphens only)",
    "description": "string",
    "theme": { "primaryColor": "#hex", "mode": "dark|light" }
  },
  "backend": {
    "generator": "amplication",
    "settings": { "generateREST": true, "generateSwagger": true },
    "auth": { "provider": "jwt" }
  },
  "data": {
    "tables": [
      {
        "name": "string (PascalCase)",
        "displayName": "string",
        "primaryKey": "id",
        "columns": [
          { "name": "string (camelCase)", "type": "uuid|text|int|float|bool|date|timestamptz|jsonb", "required": boolean, "default": any, "unique": boolean, "indexed": boolean }
        ]
      }
    ],
    "relationships": [
      { "name": "string (camelCase)", "type": "many_to_one|one_to_many", "fromTable": "string", "toTable": "string" }
    ]
  },
  "security": {
    "roles": [{ "name": "string", "displayName": "string" }],
    "permissions": [
      { "role": "string", "entity": "string", "actions": { "create": bool, "read": bool, "update": bool, "delete": bool } }
    ]
  },
  "ui": {
    "navigation": [{ "name": "string", "label": "string", "icon": "string", "route": "string" }],
    "pages": [
      {
        "id": "string",
        "route": "/path",
        "title": "string",
        "icon": "string",
        "layout": { "type": "single|split|grid|tabs", "config": {} },
        "blocks": [
          {
            "id": "string",
            "type": "BLOCK_TYPE",
            "dataSource": { "entity": "string (PascalCase)", "filters": [], "orderBy": [], "include": [] },
            "props": { ... block-specific props ... },
            "actions": [{ "trigger": "event", "action": "actionType", "config": {} }]
          }
        ]
      }
    ],
    "modals": [
      { "id": "string", "title": "string", "size": "small|medium|large", "blocks": [...] }
    ]
  }
}

AVAILABLE BLOCK TYPES:

1. TABLE - Data grid with sorting, filtering, pagination
   Props: { columns: [{ field, header, type, sortable }], allowCreate, allowEdit, allowDelete }
   Use for: Lists, reports, admin panels, data-heavy views

2. FORM - Dynamic form with validation
   Props: { fields: [{ name, label, type, required, options }] }
   Field types: text, textarea, number, select, checkbox, date, datetime, relation
   Use for: Create/edit dialogs, settings pages

3. DETAIL - Single record display
   Props: { fields: [{ name, label, type }], layout: "vertical|horizontal|grid" }
   Use for: Record detail views, profile pages

4. STAT_CARD - Metric display with optional trend
   Props: { title, valueField, icon, color }
   Use for: Dashboard KPIs, summary metrics

5. CHART - Various chart types
   Props: { chartType: "bar|line|pie|donut|area", xField, yField, groupField, colors, showLegend }
   Use for: Analytics, reports, data visualization

6. KANBAN - Drag-drop column board
   Props: {
     groupByField: "status_field",
     columns: [{ value, label, color }],
     card: { titleField, descriptionField, metaFields: [] },
     allowDragDrop, allowCreate
   }
   Use for: Task boards, pipelines, workflow management

7. CALENDAR - Month/week/day event views
   Props: {
     startField, endField, titleField, colorField,
     views: ["month", "week", "day"],
     defaultView, allowCreate, allowDrag
   }
   Use for: Scheduling, events, appointments

8. TIMELINE - Chronological list
   Props: { dateField, titleField, descriptionField, groupBy: "day|week|month" }
   Use for: Activity logs, history, feeds

9. CHAT - Message thread interface
   Props: { messageField, senderNameField, timestampField, allowReply }
   Use for: Messaging, comments, discussions

10. GALLERY - Image/card grid
    Props: { imageField, titleField, descriptionField, columns: 3 }
    Use for: Media galleries, product catalogs

BLOCK SELECTION GUIDELINES:

1. TASK/PROJECT MANAGEMENT → Use KANBAN as primary view
   - Group tasks by status (todo, inProgress, done)
   - Include card with title, description, assignee, dueDate

2. SCHEDULING/CALENDAR APPS → Use CALENDAR as primary view
   - Map events to start/end dates
   - Color-code by category

3. DASHBOARDS → Use GRID layout with multiple blocks
   - STAT_CARDs for KPIs at top
   - CHARTs for data visualization
   - TABLE for recent items

4. CRM/CONTACTS → Use TABLE + DETAIL combination
   - Split view: TABLE on left, DETAIL on right

NAMING CONVENTIONS (V3):

- Entity names: PascalCase (Task, Project, UserComment)
- Field names: camelCase (dueDate, isCompleted, createdBy)
- Relationship names: camelCase (project, tasks, assignedUser)
- App slug: lowercase-with-hyphens

IMPORTANT RULES:
- System columns (id, createdAt, updatedAt) are auto-added; don't include them in columns
- Entity names must be PascalCase
- Field names must be camelCase
- App slug must be lowercase with hyphens only
- Include at least 1 entity and 1 page
- Make the app practical and complete for the described use case
- ALWAYS choose the most appropriate block type for the use case
- For task/project apps, USE KANBAN. For scheduling, USE CALENDAR.
- dataSource uses "entity" (not "table") and must match entity names exactly (PascalCase)
"""

# V2 Blueprint System Prompt (legacy)
BLUEPRINT_V2_SYSTEM_PROMPT = """You are a UI architect generating application blueprints. Generate a valid BlueprintV2 JSON document for a business web application based on the user's description.

CRITICAL RULES:
1. Return ONLY valid JSON that conforms to BlueprintV2 schema. No prose, no markdown, no explanations.
2. The JSON must be parseable directly.
3. Choose appropriate UI blocks based on the application type - DO NOT default to tables for everything.

BlueprintV2 Schema:
{
  "version": 2,
  "app": {
    "name": "string",
    "slug": "string (lowercase, hyphens only)",
    "description": "string",
    "theme": { "primaryColor": "#hex", "mode": "dark|light" }
  },
  "data": {
    "tables": [
      {
        "name": "string (snake_case)",
        "primaryKey": "id",
        "columns": [
          { "name": "string", "type": "uuid|text|int|float|bool|date|timestamptz|jsonb", "required": boolean, "default": any, "unique": boolean, "indexed": boolean }
        ]
      }
    ],
    "relationships": [
      { "type": "many_to_one|one_to_many", "fromTable": "string", "fromColumn": "string", "toTable": "string", "toColumn": "string", "lookupLabelColumn": "string" }
    ]
  },
  "security": {
    "roles": ["Admin", "User"],
    "permissions": [{ "role": "string", "resource": "table_name", "actions": { "list": bool, "read": bool, "create": bool, "update": bool, "delete": bool } }],
    "rowFilters": []
  },
  "ui": {
    "navigation": [{ "name": "string", "label": "string", "icon": "string", "route": "string" }],
    "pages": [
      {
        "id": "string",
        "route": "/path",
        "title": "string",
        "icon": "string",
        "layout": { "type": "single|split|grid|tabs", "config": {} },
        "blocks": [
          {
            "id": "string",
            "type": "BLOCK_TYPE",
            "dataSource": { "table": "string", "filters": [], "orderBy": [], "include": [] },
            "props": { ... block-specific props ... },
            "actions": [{ "trigger": "event", "action": "actionType", "config": {} }]
          }
        ]
      }
    ],
    "modals": [
      { "id": "string", "title": "string", "size": "small|medium|large", "blocks": [...] }
    ]
  }
}

IMPORTANT RULES:
- System columns (id, created_at, updated_at, created_by) are auto-added; don't include them in columns
- Table names must be snake_case
- App slug must be lowercase with hyphens only
- Include at least 1 table and 1 page
"""


class LLMService:
   def __init__(self):
      self.api_key = settings.OPENROUTER_API_KEY
      self.base_url = settings.OPENROUTER_BASE_URL
      self.default_model = settings.LLM_MODEL

   async def generate_blueprint(
      self,
      prompt: str,
      model: Optional[str] = None,
      version: int = 3
   ) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
      """
      Generate a blueprint from a natural language prompt.
      Returns: (blueprint_dict, llm_request, llm_response)
      """
      model = model or self.default_model
      
      # Select system prompt based on version
      system_prompt = BLUEPRINT_V3_SYSTEM_PROMPT if version == 3 else BLUEPRINT_V2_SYSTEM_PROMPT

      messages = [
         {"role": "system", "content": system_prompt},
         {"role": "user", "content": f"Create a business application for: {prompt}"}
      ]

      request_payload = {
         "model": model,
         "messages": messages,
         "temperature": 0.7,
         "max_tokens": 8000,
      }

      headers = {
         "Authorization": f"Bearer {self.api_key}",
         "Content-Type": "application/json",
         "HTTP-Referer": "https://blueprint-apps-builder.local",
         "X-Title": "Blueprint Apps Builder",
      }

      async with httpx.AsyncClient(timeout=120.0) as client:
         response = await client.post(
            f"{self.base_url}/chat/completions",
            json=request_payload,
            headers=headers,
         )
         response.raise_for_status()
         response_data = response.json()

      # Extract the content
      content = response_data["choices"][0]["message"]["content"]

      # Clean up the content (remove markdown code blocks if present)
      content = content.strip()
      if content.startswith("```json"):
         content = content[7:]
      if content.startswith("```"):
         content = content[3:]
      if content.endswith("```"):
         content = content[:-3]
      content = content.strip()

      # Parse JSON
      blueprint_dict = json.loads(content)

      return blueprint_dict, request_payload, response_data

   async def repair_blueprint(
      self,
      original_prompt: str,
      invalid_json: str,
      validation_errors: str,
      model: Optional[str] = None,
      version: int = 3
   ) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
      """
      Attempt to repair an invalid blueprint.
      """
      model = model or self.default_model
      
      # Select system prompt based on version
      system_prompt = BLUEPRINT_V3_SYSTEM_PROMPT if version == 3 else BLUEPRINT_V2_SYSTEM_PROMPT

      repair_prompt = f"""The previous blueprint generation had validation errors. Please fix them.

Original request: {original_prompt}

Invalid JSON:
{invalid_json}

Validation errors:
{validation_errors}

Return ONLY the corrected valid JSON. No explanations."""

      messages = [
         {"role": "system", "content": system_prompt},
         {"role": "user", "content": repair_prompt}
      ]

      request_payload = {
         "model": model,
         "messages": messages,
         "temperature": 0.3,  # Lower temperature for repairs
         "max_tokens": 8000,
      }

      headers = {
         "Authorization": f"Bearer {self.api_key}",
         "Content-Type": "application/json",
         "HTTP-Referer": "https://blueprint-apps-builder.local",
         "X-Title": "Blueprint Apps Builder",
      }

      async with httpx.AsyncClient(timeout=120.0) as client:
         response = await client.post(
            f"{self.base_url}/chat/completions",
            json=request_payload,
            headers=headers,
         )
         response.raise_for_status()
         response_data = response.json()

      content = response_data["choices"][0]["message"]["content"]

      # Clean up
      content = content.strip()
      if content.startswith("```json"):
         content = content[7:]
      if content.startswith("```"):
         content = content[3:]
      if content.endswith("```"):
         content = content[:-3]
      content = content.strip()

      blueprint_dict = json.loads(content)

      return blueprint_dict, request_payload, response_data
