import hashlib
import json
import re
import logging
from typing import Dict, Any, List, Tuple, Optional, Union
from pydantic import ValidationError

from app.schemas.blueprint import BlueprintV2, BlueprintV3, Blueprint

logger = logging.getLogger(__name__)

# Valid identifier patterns
IDENTIFIER_PATTERN_V2 = re.compile(r'^[a-z][a-z0-9_]{0,30}$')  # snake_case for V2
IDENTIFIER_PATTERN_V3 = re.compile(r'^[A-Z][a-zA-Z0-9]{0,30}$')  # PascalCase for V3
CAMEL_CASE_PATTERN = re.compile(r'^[a-z][a-zA-Z0-9]{0,30}$')  # camelCase for V3 columns
SLUG_PATTERN = re.compile(r'^[a-z][a-z0-9-]{0,30}$')


class BlueprintService:
   """Service for validating and processing blueprints."""

   def validate_blueprint(
      self, 
      blueprint_dict: Dict[str, Any]
   ) -> Tuple[bool, Optional[Union[BlueprintV2, BlueprintV3]], List[str]]:
      """
      Validate a blueprint dictionary against the appropriate schema.
      Automatically detects version and validates accordingly.
      Returns: (is_valid, parsed_blueprint, errors)
      """
      errors = []
      version = blueprint_dict.get("version", 2)

      # Try to parse based on version
      try:
         if version == 3:
            blueprint = BlueprintV3(**blueprint_dict)
            errors.extend(self._validate_v3(blueprint))
         else:
            blueprint = BlueprintV2(**blueprint_dict)
            errors.extend(self._validate_v2(blueprint))
      except ValidationError as e:
         for error in e.errors():
            loc = " -> ".join(str(x) for x in error["loc"])
            errors.append(f"{loc}: {error['msg']}")
         return False, None, errors

      if errors:
         return False, blueprint, errors

      return True, blueprint, []

   # =========================================================================
   # V2 Validation
   # =========================================================================

   def _validate_v2(self, blueprint: BlueprintV2) -> List[str]:
      """Validate BlueprintV2 specific rules."""
      errors = []
      errors.extend(self._validate_identifiers_v2(blueprint))
      errors.extend(self._validate_relationships_v2(blueprint))
      errors.extend(self._validate_pages_v2(blueprint))
      errors.extend(self._validate_permissions_v2(blueprint))
      return errors

   def _validate_identifiers_v2(self, blueprint: BlueprintV2) -> List[str]:
      """Validate that all identifiers match the required pattern (snake_case)."""
      errors = []

      # Validate app slug
      if not SLUG_PATTERN.match(blueprint.app.slug):
         errors.append(f"App slug '{blueprint.app.slug}' must be lowercase with hyphens only")

      # Validate table names
      for table in blueprint.data.tables:
         if not IDENTIFIER_PATTERN_V2.match(table.name):
            errors.append(f"Table name '{table.name}' must be snake_case (lowercase, underscores)")

         # Validate column names
         for col in table.columns:
            if not IDENTIFIER_PATTERN_V2.match(col.name):
               errors.append(f"Column name '{col.name}' in table '{table.name}' must be snake_case")

      return errors

   def _validate_relationships_v2(self, blueprint: BlueprintV2) -> List[str]:
      """Validate that relationships reference existing tables and columns."""
      errors = []
      table_names = {t.name for t in blueprint.data.tables}

      for rel in blueprint.data.relationships or []:
         if rel.fromTable not in table_names:
            errors.append(f"Relationship references non-existent table '{rel.fromTable}'")
         if rel.toTable not in table_names:
            errors.append(f"Relationship references non-existent table '{rel.toTable}'")

      return errors

   def _validate_pages_v2(self, blueprint: BlueprintV2) -> List[str]:
      """Validate that pages reference existing tables in data sources."""
      errors = []
      table_names = {t.name for t in blueprint.data.tables}

      for page in blueprint.ui.pages:
         for block in page.blocks:
            if block.dataSource and block.dataSource.table not in table_names:
               errors.append(f"Block '{block.id}' in page '{page.id}' references non-existent table '{block.dataSource.table}'")

      return errors

   def _validate_permissions_v2(self, blueprint: BlueprintV2) -> List[str]:
      """Validate that permissions reference existing roles and resources."""
      errors = []
      roles = set(blueprint.security.roles)
      table_names = {t.name for t in blueprint.data.tables}

      for perm in blueprint.security.permissions:
         if perm.role not in roles:
            errors.append(f"Permission references non-existent role '{perm.role}'")
         if perm.resource not in table_names:
            errors.append(f"Permission references non-existent table '{perm.resource}'")

      return errors

   # =========================================================================
   # V3 Validation
   # =========================================================================

   def _validate_v3(self, blueprint: BlueprintV3) -> List[str]:
      """Validate BlueprintV3 specific rules."""
      errors = []
      errors.extend(self._validate_identifiers_v3(blueprint))
      errors.extend(self._validate_relationships_v3(blueprint))
      errors.extend(self._validate_pages_v3(blueprint))
      errors.extend(self._validate_permissions_v3(blueprint))
      errors.extend(self._validate_backend_config(blueprint))
      return errors

   def _validate_identifiers_v3(self, blueprint: BlueprintV3) -> List[str]:
      """Validate that all identifiers match V3 patterns (PascalCase for entities, camelCase for fields)."""
      errors = []

      # Validate app slug
      if not SLUG_PATTERN.match(blueprint.app.slug):
         errors.append(f"App slug '{blueprint.app.slug}' must be lowercase with hyphens only")

      # Validate entity names (PascalCase)
      for table in blueprint.data.tables:
         if not IDENTIFIER_PATTERN_V3.match(table.name):
            errors.append(f"Entity name '{table.name}' must be PascalCase (e.g., 'Task', 'UserProject')")

         # Validate column names (camelCase)
         for col in table.columns:
            if not CAMEL_CASE_PATTERN.match(col.name):
               errors.append(f"Field name '{col.name}' in entity '{table.name}' must be camelCase")

      return errors

   def _validate_relationships_v3(self, blueprint: BlueprintV3) -> List[str]:
      """Validate that relationships reference existing entities."""
      errors = []
      entity_names = {t.name for t in blueprint.data.tables}

      for rel in blueprint.data.relationships or []:
         if rel.fromTable not in entity_names:
            errors.append(f"Relationship references non-existent entity '{rel.fromTable}'")
         if rel.toTable not in entity_names:
            errors.append(f"Relationship references non-existent entity '{rel.toTable}'")

      return errors

   def _validate_pages_v3(self, blueprint: BlueprintV3) -> List[str]:
      """Validate that pages reference existing entities in data sources."""
      errors = []
      entity_names = {t.name for t in blueprint.data.tables}

      for page in blueprint.ui.pages:
         for block in page.blocks:
            if block.dataSource and block.dataSource.entity not in entity_names:
               errors.append(f"Block '{block.id}' in page '{page.id}' references non-existent entity '{block.dataSource.entity}'")

      return errors

   def _validate_permissions_v3(self, blueprint: BlueprintV3) -> List[str]:
      """Validate that permissions reference existing roles and entities."""
      errors = []
      roles = {r.name for r in blueprint.security.roles}
      entity_names = {t.name for t in blueprint.data.tables}

      for perm in blueprint.security.permissions:
         if perm.role not in roles:
            errors.append(f"Permission references non-existent role '{perm.role}'")
         if perm.entity not in entity_names:
            errors.append(f"Permission references non-existent entity '{perm.entity}'")

      return errors

   def _validate_backend_config(self, blueprint: BlueprintV3) -> List[str]:
      """Validate backend configuration."""
      errors = []
      
      # Currently only amplication is supported
      if blueprint.backend.generator != "amplication":
         errors.append(f"Unsupported backend generator: {blueprint.backend.generator}")

      return errors

   # =========================================================================
   # Common utilities
   # =========================================================================

   def compute_hash(self, blueprint_dict: Dict[str, Any]) -> str:
      """Compute a hash of the blueprint for change detection."""
      json_str = json.dumps(blueprint_dict, sort_keys=True)
      return hashlib.sha256(json_str.encode()).hexdigest()

   def get_tables_in_dependency_order(self, blueprint: Union[BlueprintV2, BlueprintV3]) -> List[str]:
      """
      Return table/entity names in order that respects foreign key dependencies.
      Tables without FKs come first.
      """
      tables = {t.name: t for t in blueprint.data.tables}
      dependencies = {t.name: set() for t in blueprint.data.tables}

      # Build dependency graph from relationships
      for rel in blueprint.data.relationships or []:
         if rel.type == "many_to_one":
            # fromTable depends on toTable
            if rel.fromTable in dependencies:
               dependencies[rel.fromTable].add(rel.toTable)

      # Topological sort
      ordered = []
      visited = set()
      temp_visited = set()

      def visit(name: str):
         if name in temp_visited:
            raise ValueError(f"Circular dependency detected involving {name}")
         if name in visited:
            return
         temp_visited.add(name)
         for dep in dependencies.get(name, []):
            if dep in tables:
               visit(dep)
         temp_visited.remove(name)
         visited.add(name)
         ordered.append(name)

      for table_name in tables:
         if table_name not in visited:
            visit(table_name)

      return ordered

   def is_v3(self, blueprint_dict: Dict[str, Any]) -> bool:
      """Check if blueprint is V3."""
      return blueprint_dict.get("version") == 3

   def convert_v2_to_v3(self, blueprint_v2: BlueprintV2) -> Dict[str, Any]:
      """
      Convert a V2 blueprint to V3 format.
      This is a helper for migration.
      """
      # Convert snake_case to PascalCase for entity names
      def to_pascal_case(name: str) -> str:
         return ''.join(word.capitalize() for word in name.split('_'))
      
      # Convert snake_case to camelCase for field names
      def to_camel_case(name: str) -> str:
         parts = name.split('_')
         return parts[0] + ''.join(word.capitalize() for word in parts[1:])

      v3_dict = {
         "version": 3,
         "app": blueprint_v2.app.model_dump(),
         "backend": {
            "generator": "amplication",
            "settings": {
               "generateREST": True,
               "generateSwagger": True
            },
            "auth": {
               "provider": "jwt"
            }
         },
         "data": {
            "tables": [],
            "relationships": []
         },
         "security": {
            "roles": [],
            "permissions": []
         },
         "ui": blueprint_v2.ui.model_dump()
      }

      # Convert tables
      for table in blueprint_v2.data.tables:
         v3_table = {
            "name": to_pascal_case(table.name),
            "displayName": to_pascal_case(table.name),
            "primaryKey": "id",
            "columns": []
         }
         for col in table.columns:
            v3_table["columns"].append({
               "name": to_camel_case(col.name),
               "type": col.type,
               "required": col.required,
               "default": col.default,
               "unique": col.unique,
               "indexed": col.indexed
            })
         v3_dict["data"]["tables"].append(v3_table)

      # Convert relationships
      for rel in blueprint_v2.data.relationships or []:
         v3_dict["data"]["relationships"].append({
            "name": to_camel_case(rel.fromColumn.replace('_id', '')),
            "type": rel.type,
            "fromTable": to_pascal_case(rel.fromTable),
            "toTable": to_pascal_case(rel.toTable)
         })

      # Convert security
      for role in blueprint_v2.security.roles:
         v3_dict["security"]["roles"].append({
            "name": role,
            "displayName": role
         })

      for perm in blueprint_v2.security.permissions:
         v3_dict["security"]["permissions"].append({
            "role": perm.role,
            "entity": to_pascal_case(perm.resource),
            "actions": perm.actions
         })

      # Update UI data sources to use "entity" instead of "table"
      for page in v3_dict["ui"]["pages"]:
         for block in page.get("blocks", []):
            if block.get("dataSource") and "table" in block["dataSource"]:
               block["dataSource"]["entity"] = to_pascal_case(block["dataSource"]["table"])
               del block["dataSource"]["table"]

      return v3_dict
