import hashlib
import json
import re
import logging
from typing import Dict, Any, List, Tuple, Optional
from pydantic import ValidationError

from app.schemas.blueprint import BlueprintV2

logger = logging.getLogger(__name__)

# Valid identifier pattern
IDENTIFIER_PATTERN = re.compile(r'^[a-z][a-z0-9_]{0,30}$')
SLUG_PATTERN = re.compile(r'^[a-z][a-z0-9-]{0,30}$')


class BlueprintService:
   """Service for validating and processing blueprints."""

   def validate_blueprint(self, blueprint_dict: Dict[str, Any]) -> Tuple[bool, Optional[BlueprintV2], List[str]]:
      """
      Validate a blueprint dictionary against the BlueprintV2 schema.
      Returns: (is_valid, parsed_blueprint, errors)
      """
      errors = []

      # First, try Pydantic validation
      try:
         blueprint = BlueprintV2(**blueprint_dict)
      except ValidationError as e:
         for error in e.errors():
            loc = " -> ".join(str(x) for x in error["loc"])
            errors.append(f"{loc}: {error['msg']}")
         return False, None, errors

      # Additional semantic validations
      errors.extend(self._validate_identifiers(blueprint))
      errors.extend(self._validate_relationships(blueprint))
      errors.extend(self._validate_pages(blueprint))
      errors.extend(self._validate_permissions(blueprint))

      if errors:
         return False, blueprint, errors

      return True, blueprint, []

   def _validate_identifiers(self, blueprint: BlueprintV2) -> List[str]:
      """Validate that all identifiers match the required pattern."""
      errors = []

      # Validate app slug
      if not SLUG_PATTERN.match(blueprint.app.slug):
         errors.append(f"App slug '{blueprint.app.slug}' must be lowercase with hyphens only")

      # Validate table names
      for table in blueprint.data.tables:
         if not IDENTIFIER_PATTERN.match(table.name):
            errors.append(f"Table name '{table.name}' must be snake_case (lowercase, underscores)")

         # Validate column names
         for col in table.columns:
            if not IDENTIFIER_PATTERN.match(col.name):
               errors.append(f"Column name '{col.name}' in table '{table.name}' must be snake_case")

      return errors

   def _validate_relationships(self, blueprint: BlueprintV2) -> List[str]:
      """Validate that relationships reference existing tables and columns."""
      errors = []
      table_names = {t.name for t in blueprint.data.tables}

      for rel in blueprint.data.relationships or []:
         if rel.fromTable not in table_names:
            errors.append(f"Relationship references non-existent table '{rel.fromTable}'")
         if rel.toTable not in table_names:
            errors.append(f"Relationship references non-existent table '{rel.toTable}'")

      return errors

   def _validate_pages(self, blueprint: BlueprintV2) -> List[str]:
      """Validate that pages reference existing tables in data sources."""
      errors = []
      table_names = {t.name for t in blueprint.data.tables}

      for page in blueprint.ui.pages:
         for block in page.blocks:
            if block.dataSource and block.dataSource.table not in table_names:
               errors.append(f"Block '{block.id}' in page '{page.id}' references non-existent table '{block.dataSource.table}'")

      return errors

   def _validate_permissions(self, blueprint: BlueprintV2) -> List[str]:
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

   def compute_hash(self, blueprint_dict: Dict[str, Any]) -> str:
      """Compute a hash of the blueprint for change detection."""
      json_str = json.dumps(blueprint_dict, sort_keys=True)
      return hashlib.sha256(json_str.encode()).hexdigest()

   def get_tables_in_dependency_order(self, blueprint: BlueprintV2) -> List[str]:
      """
      Return table names in order that respects foreign key dependencies.
      Tables without FKs come first.
      """
      tables = {t.name: t for t in blueprint.data.tables}
      dependencies = {t.name: set() for t in blueprint.data.tables}

      # Build dependency graph from relationships
      for rel in blueprint.data.relationships or []:
         if rel.type == "many_to_one":
            # fromTable depends on toTable
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

