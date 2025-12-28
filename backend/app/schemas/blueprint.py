from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional, List, Dict, Any, Literal
from app.models.blueprint import ValidationStatus


# Blueprint V1 Schema
class ColumnSpec(BaseModel):
   name: str
   type: Literal["uuid", "text", "int", "float", "bool", "date", "timestamptz", "jsonb"]
   required: bool = False
   default: Optional[Any] = None
   unique: bool = False
   indexed: bool = False


class TableSpec(BaseModel):
   name: str
   primaryKey: str = "id"
   columns: List[ColumnSpec]


class RelationshipSpec(BaseModel):
   type: Literal["many_to_one", "one_to_many"]
   fromTable: str
   fromColumn: str
   toTable: str
   toColumn: str
   lookupLabelColumn: Optional[str] = None


class PermissionRule(BaseModel):
   role: str
   resource: str
   actions: Dict[str, bool]  # list, read, create, update, delete


class FilterExpression(BaseModel):
   equals: Optional[List[str]] = None
   in_: Optional[List[str]] = Field(None, alias="in")
   and_: Optional[List["FilterExpression"]] = Field(None, alias="and")
   or_: Optional[List["FilterExpression"]] = Field(None, alias="or")

   class Config:
      populate_by_name = True


class RowFilterRule(BaseModel):
   role: str
   resource: str
   filter: FilterExpression


class FieldSpec(BaseModel):
   name: str
   widget: Optional[str] = None
   options: Optional[List[Any]] = None
   label: Optional[str] = None


class ListConfig(BaseModel):
   columns: List[str]
   filters: Optional[List[Dict[str, Any]]] = None


class FormConfig(BaseModel):
   createFields: Optional[List[FieldSpec]] = None
   editFields: Optional[List[FieldSpec]] = None


class ResourceSpec(BaseModel):
   name: str
   table: str
   label: str
   views: Dict[str, bool] = {"list": True, "create": True, "edit": True, "show": True}
   list: Optional[ListConfig] = None
   forms: Optional[FormConfig] = None


class NavItem(BaseModel):
   name: str
   label: str
   icon: Optional[str] = None
   route: Optional[str] = None
   children: Optional[List["NavItem"]] = None


class AppInfo(BaseModel):
   name: str
   slug: str
   description: Optional[str] = None


class DataSpec(BaseModel):
   tables: List[TableSpec]
   relationships: Optional[List[RelationshipSpec]] = []


class SecuritySpec(BaseModel):
   roles: List[str]
   permissions: List[PermissionRule]
   rowFilters: Optional[List[RowFilterRule]] = []


class UISpec(BaseModel):
   navigation: List[NavItem]
   resources: List[ResourceSpec]
   pages: Optional[List[Dict[str, Any]]] = []


class BlueprintV1(BaseModel):
   version: int = 1
   app: AppInfo
   data: DataSpec
   security: SecuritySpec
   ui: UISpec


# Response schemas
class BlueprintResponse(BaseModel):
   id: UUID
   app_id: UUID
   version: int
   blueprint_json: Dict[str, Any]
   blueprint_hash: Optional[str]
   validation_status: ValidationStatus
   validation_errors: Optional[Dict[str, Any]]
   created_at: datetime

   class Config:
      from_attributes = True

