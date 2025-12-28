import httpx
import json
import logging
from typing import Dict, Any, Optional, Tuple

from app.config import settings
from app.schemas.blueprint import BlueprintV1

logger = logging.getLogger(__name__)

BLUEPRINT_SYSTEM_PROMPT = """You are a business application architect. Generate a valid BlueprintV1 JSON document for a business web application based on the user's description.

CRITICAL RULES:
1. Return ONLY valid JSON that conforms to BlueprintV1 schema. No prose, no markdown, no explanations.
2. The JSON must be parseable directly.

BlueprintV1 Schema:
{
  "version": 1,
  "app": { "name": "string", "slug": "string (lowercase, hyphens only)", "description": "string" },
  "data": {
    "tables": [
      {
        "name": "string (snake_case)",
        "primaryKey": "id",
        "columns": [
          {
            "name": "string",
            "type": "uuid|text|int|float|bool|date|timestamptz|jsonb",
            "required": boolean,
            "default": any (optional),
            "unique": boolean,
            "indexed": boolean
          }
        ]
      }
    ],
    "relationships": [
      {
        "type": "many_to_one|one_to_many",
        "fromTable": "string",
        "fromColumn": "string",
        "toTable": "string",
        "toColumn": "string",
        "lookupLabelColumn": "string (optional)"
      }
    ]
  },
  "security": {
    "roles": ["Admin", "User", ...],
    "permissions": [
      {
        "role": "string",
        "resource": "table_name",
        "actions": { "list": bool, "read": bool, "create": bool, "update": bool, "delete": bool }
      }
    ],
    "rowFilters": []
  },
  "ui": {
    "navigation": [
      { "name": "string", "label": "string", "icon": "string (optional)", "route": "string" }
    ],
    "resources": [
      {
        "name": "string",
        "table": "table_name",
        "label": "string",
        "views": { "list": true, "create": true, "edit": true, "show": true },
        "list": { "columns": ["column_name", ...] },
        "forms": {
          "createFields": [{ "name": "column_name", "widget": "text|select|checkbox|date|number", "label": "string" }],
          "editFields": [{ "name": "column_name", "widget": "text|select|checkbox|date|number", "label": "string" }]
        }
      }
    ],
    "pages": []
  }
}

IMPORTANT:
- System columns (id, created_at, updated_at, created_by) are auto-added; don't include them in columns.
- Table names must be snake_case
- App slug must be lowercase with hyphens only
- Include at least 1 table, 1 role, and 1 resource
- Every table should have a corresponding resource in ui.resources
- Make the app practical and complete for the described use case
"""


class LLMService:
   def __init__(self):
      self.api_key = settings.OPENROUTER_API_KEY
      self.base_url = settings.OPENROUTER_BASE_URL
      self.default_model = settings.DEFAULT_LLM_MODEL

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
         "max_tokens": 4000,
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
         "max_tokens": 4000,
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

