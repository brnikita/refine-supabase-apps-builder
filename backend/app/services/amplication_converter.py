"""
AmplicationConverter: Converts BlueprintV3 to Amplication entity format.

This service transforms our Blueprint schema into the format required by
Amplication for code generation.
"""

import logging
from typing import Dict, Any, List
from app.schemas.blueprint import BlueprintV3, TableSpec, ColumnSpec, RelationshipSpec

logger = logging.getLogger(__name__)


# Type mapping from Blueprint to Amplication
BLUEPRINT_TO_AMPLICATION_TYPE: Dict[str, str] = {
    "uuid": "Id",
    "text": "SingleLineText",
    "int": "WholeNumber",
    "float": "DecimalNumber",
    "bool": "Boolean",
    "date": "DateTime",
    "timestamptz": "DateTime",
    "jsonb": "Json",
}


class AmplicationConverter:
    """Converts BlueprintV3 to Amplication entities format."""

    def convert(self, blueprint: BlueprintV3) -> Dict[str, Any]:
        """
        Convert a BlueprintV3 to Amplication project configuration.
        
        Returns a dictionary with:
        - entities: List of Amplication entity definitions
        - roles: List of role definitions
        - permissions: Entity permissions
        """
        return {
            "project": {
                "name": blueprint.app.name,
                "description": blueprint.app.description or "",
            },
            "entities": self._convert_entities(blueprint),
            "roles": self._convert_roles(blueprint),
            "entityPermissions": self._convert_permissions(blueprint),
        }

    def _convert_entities(self, blueprint: BlueprintV3) -> List[Dict[str, Any]]:
        """Convert Blueprint tables to Amplication entities."""
        entities = []
        
        # Build relationship map for quick lookup
        relationship_map = self._build_relationship_map(blueprint.data.relationships or [])
        
        for table in blueprint.data.tables:
            entity = {
                "name": table.name,
                "displayName": table.displayName or table.name,
                "pluralDisplayName": f"{table.displayName or table.name}s",
                "fields": self._convert_fields(table, relationship_map.get(table.name, [])),
            }
            entities.append(entity)
        
        return entities

    def _convert_fields(
        self, 
        table: TableSpec, 
        relationships: List[RelationshipSpec]
    ) -> List[Dict[str, Any]]:
        """Convert Blueprint columns to Amplication fields."""
        fields = []
        
        # Add ID field (always required)
        fields.append({
            "name": "id",
            "displayName": "ID",
            "dataType": "Id",
            "required": True,
            "unique": True,
            "searchable": False,
        })
        
        # Add regular columns
        for col in table.columns:
            field = {
                "name": col.name,
                "displayName": self._to_display_name(col.name),
                "dataType": BLUEPRINT_TO_AMPLICATION_TYPE.get(col.type, "SingleLineText"),
                "required": col.required,
                "unique": col.unique,
                "searchable": col.indexed,
            }
            
            # Add default value if specified
            if col.default is not None:
                field["customAttributes"] = f'@default("{col.default}")'
            
            fields.append(field)
        
        # Add relationship fields
        for rel in relationships:
            if rel.type == "many_to_one":
                # Add foreign key field
                fields.append({
                    "name": rel.name,
                    "displayName": self._to_display_name(rel.name),
                    "dataType": "Lookup",
                    "required": False,
                    "searchable": True,
                    "properties": {
                        "relatedEntityId": rel.toTable,
                        "allowMultipleSelection": False,
                    }
                })
        
        # Add timestamp fields
        fields.extend([
            {
                "name": "createdAt",
                "displayName": "Created At",
                "dataType": "CreatedAt",
                "required": True,
                "searchable": False,
            },
            {
                "name": "updatedAt",
                "displayName": "Updated At",
                "dataType": "UpdatedAt",
                "required": True,
                "searchable": False,
            },
        ])
        
        return fields

    def _convert_roles(self, blueprint: BlueprintV3) -> List[Dict[str, Any]]:
        """Convert Blueprint roles to Amplication roles."""
        roles = []
        
        for role in blueprint.security.roles:
            roles.append({
                "name": role.name,
                "displayName": role.displayName or role.name,
            })
        
        return roles

    def _convert_permissions(self, blueprint: BlueprintV3) -> List[Dict[str, Any]]:
        """Convert Blueprint permissions to Amplication entity permissions."""
        permissions = []
        
        for perm in blueprint.security.permissions:
            entity_perm = {
                "entityName": perm.entity,
                "roleName": perm.role,
                "permissions": {
                    "create": {"type": "Allow" if perm.actions.get("create") else "Deny"},
                    "read": {"type": "Allow" if perm.actions.get("read") else "Deny"},
                    "update": {"type": "Allow" if perm.actions.get("update") else "Deny"},
                    "delete": {"type": "Allow" if perm.actions.get("delete") else "Deny"},
                }
            }
            permissions.append(entity_perm)
        
        return permissions

    def _build_relationship_map(
        self, 
        relationships: List[RelationshipSpec]
    ) -> Dict[str, List[RelationshipSpec]]:
        """Build a map of table name to its relationships."""
        rel_map: Dict[str, List[RelationshipSpec]] = {}
        
        for rel in relationships:
            if rel.fromTable not in rel_map:
                rel_map[rel.fromTable] = []
            rel_map[rel.fromTable].append(rel)
        
        return rel_map

    def _to_display_name(self, name: str) -> str:
        """Convert camelCase or snake_case to Display Name."""
        # Handle camelCase
        import re
        result = re.sub(r'([a-z])([A-Z])', r'\1 \2', name)
        # Handle snake_case
        result = result.replace('_', ' ')
        # Capitalize each word
        return result.title()

    def generate_prisma_schema(self, blueprint: BlueprintV3) -> str:
        """
        Generate Prisma schema from Blueprint.
        This is used for direct database schema generation without Amplication.
        """
        lines = [
            "// Prisma schema generated from Blueprint",
            "",
            "generator client {",
            '  provider = "prisma-client-js"',
            "}",
            "",
            "datasource db {",
            '  provider = "postgresql"',
            '  url      = env("DATABASE_URL")',
            "}",
            "",
        ]
        
        # Build relationship maps
        # many_to_one: fromTable has FK pointing to toTable
        many_to_one_map: Dict[str, List[RelationshipSpec]] = {}
        # reverse_relation_map: toTable has array of fromTable items (auto-generated from many_to_one)
        reverse_relation_map: Dict[str, List[RelationshipSpec]] = {}
        
        for rel in (blueprint.data.relationships or []):
            if rel.type == "many_to_one":
                # Task (fromTable) has FK to Project (toTable)
                if rel.fromTable not in many_to_one_map:
                    many_to_one_map[rel.fromTable] = []
                many_to_one_map[rel.fromTable].append(rel)
                
                # Auto-create reverse relation: Project needs tasks Task[]
                if rel.toTable not in reverse_relation_map:
                    reverse_relation_map[rel.toTable] = []
                reverse_relation_map[rel.toTable].append(rel)
        
        for table in blueprint.data.tables:
            lines.append(f"model {table.name} {{")
            lines.append("  id        String   @id @default(cuid())")
            
            # Collect column names to track what we've added
            added_fields = {"id"}
            
            # Get relations for this table
            many_to_one_rels = many_to_one_map.get(table.name, [])
            # Get reverse relations (other tables pointing to this one)
            reverse_rels = reverse_relation_map.get(table.name, [])
            
            # Find columns that should be skipped because they're handled by relations
            columns_from_rels = set()
            for rel in many_to_one_rels:
                # Skip both the relation name and the FK column name
                columns_from_rels.add(rel.name)  # e.g., "project"
                columns_from_rels.add(f"{rel.name}Id")  # e.g., "projectId"
            
            # Add regular columns (excluding columns that will be handled by relations)
            for col in table.columns:
                if col.name in added_fields:
                    continue
                # Skip columns that will be added with relations
                if col.name in columns_from_rels:
                    continue
                    
                prisma_type = self._to_prisma_type(col.type)
                optional = "" if col.required else "?"
                default = ""
                if col.default is not None:
                    if isinstance(col.default, str):
                        default = f' @default("{col.default}")'
                    elif isinstance(col.default, bool):
                        default = f" @default({str(col.default).lower()})"
                    else:
                        default = f" @default({col.default})"
                unique = " @unique" if col.unique else ""
                
                lines.append(f"  {col.name}  {prisma_type}{optional}{default}{unique}")
                added_fields.add(col.name)
            
            # Add many-to-one relationships (this table has FK to another table)
            for rel in many_to_one_rels:
                fk_column = f"{rel.name}Id"
                # Add relation field with explicit relation name to avoid ambiguity
                rel_name = f"{table.name}_{rel.name}"
                lines.append(f"  {rel.name}    {rel.toTable}?  @relation(\"{rel_name}\", fields: [{fk_column}], references: [id])")
                lines.append(f"  {fk_column}  String?")
                added_fields.add(rel.name)
                added_fields.add(fk_column)
            
            # Add reverse relations (this table is referenced by other tables via many_to_one)
            for rel in reverse_rels:
                # rel is a many_to_one from another table pointing to this one
                # We need to add an array field for the reverse relation
                rel_name = f"{rel.fromTable}_{rel.name}"
                # Use the fromTable name in lowercase + 's' as the field name
                field_name = f"{rel.fromTable.lower()}s"
                lines.append(f"  {field_name}  {rel.fromTable}[]  @relation(\"{rel_name}\")")
                added_fields.add(field_name)
            
            # Add timestamps
            lines.append("  createdAt DateTime @default(now())")
            lines.append("  updatedAt DateTime @updatedAt")
            lines.append("}")
            lines.append("")
        
        return "\n".join(lines)

    def _build_reverse_relationship_map(
        self, 
        relationships: List[RelationshipSpec]
    ) -> Dict[str, List[RelationshipSpec]]:
        """Build a map of table name to relationships pointing TO it."""
        rel_map: Dict[str, List[RelationshipSpec]] = {}
        
        for rel in relationships:
            if rel.toTable not in rel_map:
                rel_map[rel.toTable] = []
            rel_map[rel.toTable].append(rel)
        
        return rel_map

    def _to_prisma_type(self, blueprint_type: str) -> str:
        """Convert Blueprint type to Prisma type."""
        type_map = {
            "uuid": "String",
            "text": "String",
            "int": "Int",
            "float": "Float",
            "bool": "Boolean",
            "date": "DateTime",
            "timestamptz": "DateTime",
            "jsonb": "Json",
        }
        return type_map.get(blueprint_type, "String")

