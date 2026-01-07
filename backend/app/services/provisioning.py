import logging
from typing import Dict, Any
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.schemas.blueprint import BlueprintV2, TableSpec, ColumnSpec

logger = logging.getLogger(__name__)

# Type mapping from Blueprint to PostgreSQL
TYPE_MAPPING = {
   "uuid": "UUID",
   "text": "TEXT",
   "int": "INTEGER",
   "float": "DOUBLE PRECISION",
   "bool": "BOOLEAN",
   "date": "DATE",
   "timestamptz": "TIMESTAMPTZ",
   "jsonb": "JSONB",
}


class ProvisioningService:
   """Service for provisioning database schemas from blueprints."""

   def __init__(self, db: Session):
      self.db = db

   def provision_app_schema(self, schema_name: str, blueprint: BlueprintV2) -> None:
      """Create the database schema and tables for an app."""
      logger.info(f"Provisioning schema: {schema_name}")

      # Create schema
      self._create_schema(schema_name)

      # Get tables in dependency order
      from app.services.blueprint import BlueprintService
      bp_service = BlueprintService()
      table_order = bp_service.get_tables_in_dependency_order(blueprint)

      # Create tables
      tables_by_name = {t.name: t for t in blueprint.data.tables}
      for table_name in table_order:
         table = tables_by_name[table_name]
         self._create_table(schema_name, table)

      # Add foreign key constraints
      for rel in blueprint.data.relationships or []:
         if rel.type == "many_to_one":
            self._add_foreign_key(
               schema_name,
               rel.fromTable,
               rel.fromColumn,
               rel.toTable,
               rel.toColumn
            )

      # Enable RLS on all tables
      for table in blueprint.data.tables:
         self._enable_rls(schema_name, table.name)

      self.db.commit()
      logger.info(f"Schema {schema_name} provisioned successfully")

   def _create_schema(self, schema_name: str) -> None:
      """Create a new schema."""
      # Validate schema name to prevent SQL injection
      if not schema_name.replace("_", "").isalnum():
         raise ValueError(f"Invalid schema name: {schema_name}")

      self.db.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'))
      logger.info(f"Created schema: {schema_name}")

   def _create_table(self, schema_name: str, table: TableSpec) -> None:
      """Create a table with system columns."""
      columns_sql = []

      # System columns (always added)
      columns_sql.append("id UUID PRIMARY KEY DEFAULT gen_random_uuid()")
      columns_sql.append("created_at TIMESTAMPTZ DEFAULT now()")
      columns_sql.append("updated_at TIMESTAMPTZ DEFAULT now()")
      columns_sql.append("created_by UUID")

      # User-defined columns
      for col in table.columns:
         col_sql = self._column_to_sql(col)
         columns_sql.append(col_sql)

      columns_str = ",\n   ".join(columns_sql)
      sql = f'CREATE TABLE IF NOT EXISTS "{schema_name}"."{table.name}" (\n   {columns_str}\n)'

      self.db.execute(text(sql))
      logger.info(f"Created table: {schema_name}.{table.name}")

      # Create indexes for indexed columns
      for col in table.columns:
         if col.indexed:
            idx_name = f"idx_{table.name}_{col.name}"
            idx_sql = f'CREATE INDEX IF NOT EXISTS "{idx_name}" ON "{schema_name}"."{table.name}" ("{col.name}")'
            self.db.execute(text(idx_sql))

   def _column_to_sql(self, col: ColumnSpec) -> str:
      """Convert a column spec to SQL."""
      pg_type = TYPE_MAPPING.get(col.type, "TEXT")
      parts = [f'"{col.name}"', pg_type]

      if col.required:
         parts.append("NOT NULL")
      if col.unique:
         parts.append("UNIQUE")
      if col.default is not None:
         if isinstance(col.default, str):
            parts.append(f"DEFAULT '{col.default}'")
         elif isinstance(col.default, bool):
            parts.append(f"DEFAULT {str(col.default).lower()}")
         else:
            parts.append(f"DEFAULT {col.default}")

      return " ".join(parts)

   def _add_foreign_key(
      self,
      schema_name: str,
      from_table: str,
      from_column: str,
      to_table: str,
      to_column: str
   ) -> None:
      """Add a foreign key constraint."""
      constraint_name = f"fk_{from_table}_{from_column}"
      sql = f'''
         ALTER TABLE "{schema_name}"."{from_table}"
         ADD CONSTRAINT "{constraint_name}"
         FOREIGN KEY ("{from_column}")
         REFERENCES "{schema_name}"."{to_table}" ("{to_column}")
      '''
      try:
         self.db.execute(text(sql))
         logger.info(f"Added FK: {from_table}.{from_column} -> {to_table}.{to_column}")
      except Exception as e:
         logger.warning(f"Could not add FK {constraint_name}: {e}")

   def _enable_rls(self, schema_name: str, table_name: str) -> None:
      """Enable Row Level Security on a table."""
      sql = f'ALTER TABLE "{schema_name}"."{table_name}" ENABLE ROW LEVEL SECURITY'
      try:
         self.db.execute(text(sql))
         logger.info(f"Enabled RLS on {schema_name}.{table_name}")
      except Exception as e:
         logger.warning(f"Could not enable RLS: {e}")

   def drop_app_schema(self, schema_name: str) -> None:
      """Drop an app's schema and all its tables."""
      if not schema_name.replace("_", "").isalnum():
         raise ValueError(f"Invalid schema name: {schema_name}")

      sql = f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE'
      self.db.execute(text(sql))
      self.db.commit()
      logger.info(f"Dropped schema: {schema_name}")

