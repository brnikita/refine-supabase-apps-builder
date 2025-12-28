import httpx
import json
import logging
from typing import Dict, Any, Optional, Tuple

from app.config import settings
from app.schemas.blueprint import BlueprintV2

logger = logging.getLogger(__name__)

BLUEPRINT_SYSTEM_PROMPT = """You are a UI architect generating application blueprints. Generate a valid BlueprintV2 JSON document for a business web application based on the user's description.

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

AVAILABLE BLOCK TYPES:

1. TABLE - Data grid with sorting, filtering, pagination
   Props: { columns: [{ field, label, type, sortable }], allowSearch, allowFilter, allowSort, rowActions: ["edit", "delete"] }
   Use for: Lists, reports, admin panels, data-heavy views

2. FORM - Dynamic form with validation
   Props: { mode: "create|edit", fields: [{ name, label, type, required, options }] }
   Field types: text, textarea, number, select, checkbox, date, datetime, relation, file
   Use for: Create/edit dialogs, settings pages

3. DETAIL - Single record display
   Props: { fields: [{ name, label, type }], layout: "vertical|horizontal|grid" }
   Use for: Record detail views, profile pages

4. STAT-CARD - Metric display with optional trend
   Props: { title, value, icon, trend, trendDirection: "up|down", color }
   Use for: Dashboard KPIs, summary metrics

5. CHART - Various chart types
   Props: { chartType: "bar|line|pie|donut|area", xField, yField, groupField, colors, showLegend }
   Use for: Analytics, reports, data visualization

6. KANBAN - Drag-drop column board
   Props: {
     groupByField: "status_column",
     columns: [{ value, label, color }],
     card: { titleField, descriptionField, metaFields: [], badgeField, badgeColors: {} },
     allowDragDrop, allowCreate
   }
   Use for: Task boards, pipelines, workflow management, project tracking

7. CALENDAR - Month/week/day event views
   Props: {
     startField, endField, titleField, colorField,
     colors: { "category": "#color" },
     views: ["month", "week", "day"],
     defaultView, allowCreate, allowDrag, allowResize
   }
   Use for: Scheduling, events, appointments, bookings

8. TIMELINE - Chronological list
   Props: { dateField, titleField, descriptionField, groupBy: "day|week|month", showTime }
   Use for: Activity logs, history, feeds, notifications

9. CHAT - Message thread interface
   Props: {
     messageField, senderNameField, senderAvatarField, timestampField,
     allowReply, allowReactions, allowAttachments, realtime
   }
   Use for: Messaging, comments, discussions, support

10. GALLERY - Image/card grid
    Props: { imageField, titleField, descriptionField, columns: 3, aspectRatio: "1:1|16:9|4:3" }
    Use for: Media galleries, product catalogs, portfolios

11. TREE - Hierarchical list
    Props: { titleField, parentField, iconField, expandable }
    Use for: Categories, folders, org charts, nested navigation

12. FILE-LIST - File management
    Props: { nameField, sizeField, typeField, allowUpload, allowDownload, allowDelete }
    Use for: Document management, attachments

BLOCK SELECTION GUIDELINES:

1. TASK/PROJECT MANAGEMENT → Use KANBAN as primary view
   - Group tasks by status (backlog, todo, in_progress, done)
   - Include card with title, description, assignee, due date
   - Add TABLE view as secondary for list view

2. SCHEDULING/CALENDAR APPS → Use CALENDAR as primary view
   - Map events to start/end dates
   - Color-code by category
   - Include TIMELINE for upcoming events

3. CHAT/MESSAGING APPS → Use CHAT as primary view
   - Split layout with channel/contact list (TREE) + messages (CHAT)
   - Enable realtime updates

4. DASHBOARDS → Use GRID layout with multiple blocks
   - STAT-CARDs for KPIs at top
   - CHARTs for data visualization
   - TABLE for recent items

5. CRM/CONTACTS → Use TABLE + DETAIL combination
   - Split view: TABLE on left, DETAIL on right
   - TIMELINE for activity history

6. INVENTORY/CATALOG → Use TABLE or GALLERY
   - GALLERY for visual products
   - TABLE for data-heavy inventory

7. CONTENT/NOTES → Use TIMELINE or GALLERY
   - Rich display of content items

LAYOUT GUIDELINES:

- "single": Full-width, stacked blocks (default)
- "split": { "sizes": [30, 70], "direction": "horizontal" } - Master-detail pattern
- "grid": { "columns": 4, "gap": "16px" } - Dashboard layouts
- "tabs": { "tabs": [{ "id": "tab1", "label": "Tab 1" }] } - Multi-view pages

ACTION EXAMPLES:

- { "trigger": "cardClick", "action": "openModal", "config": { "modal": "detail-modal" } }
- { "trigger": "rowClick", "action": "navigate", "config": { "route": "/items/{{id}}" } }
- { "trigger": "submit", "action": "createRecord", "config": {} }
- { "trigger": "cardMove", "action": "updateRecord", "config": { "field": "status" } }

IMPORTANT RULES:
- System columns (id, created_at, updated_at, created_by) are auto-added; don't include them in columns
- Table names must be snake_case
- App slug must be lowercase with hyphens only
- Include at least 1 table and 1 page
- Make the app practical and complete for the described use case
- ALWAYS choose the most appropriate block type for the use case - don't default to TABLE
- For task/project apps, USE KANBAN. For scheduling, USE CALENDAR. For chat, USE CHAT.
"""


class LLMService:
   def __init__(self):
      self.api_key = settings.OPENROUTER_API_KEY
      self.base_url = settings.OPENROUTER_BASE_URL
      self.default_model = settings.LLM_MODEL

   async def generate_blueprint(
      self,
      prompt: str,
      model: Optional[str] = None
   ) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
      """
      Generate a blueprint from a natural language prompt.
      Returns: (blueprint_dict, llm_request, llm_response)
      """
      model = model or self.default_model

      messages = [
         {"role": "system", "content": BLUEPRINT_SYSTEM_PROMPT},
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
      model: Optional[str] = None
   ) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
      """
      Attempt to repair an invalid blueprint.
      """
      model = model or self.default_model

      repair_prompt = f"""The previous blueprint generation had validation errors. Please fix them.

Original request: {original_prompt}

Invalid JSON:
{invalid_json}

Validation errors:
{validation_errors}

Return ONLY the corrected valid JSON. No explanations."""

      messages = [
         {"role": "system", "content": BLUEPRINT_SYSTEM_PROMPT},
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
