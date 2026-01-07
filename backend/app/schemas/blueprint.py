from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional, List, Dict, Any, Literal, Union
from app.models.blueprint import ValidationStatus


# ============================================================================
# BLUEPRINT V3 SCHEMA - Full-Stack Generation with Amplication
# ============================================================================

# --- Data Layer ---

class ColumnSpec(BaseModel):
   name: str
   type: Literal["uuid", "text", "int", "float", "bool", "date", "timestamptz", "jsonb"]
   required: bool = False
   default: Optional[Any] = None
   unique: bool = False
   indexed: bool = False


class TableSpec(BaseModel):
   name: str  # PascalCase for V3 (e.g., "Task", "Project")
   displayName: Optional[str] = None
   primaryKey: str = "id"
   columns: List[ColumnSpec]


class RelationshipSpec(BaseModel):
   name: str  # Relationship name (e.g., "project", "tasks")
   type: Literal["many_to_one", "one_to_many"]
   fromTable: str
   toTable: str
   fromColumn: Optional[str] = None  # Optional, auto-generated if not provided
   toColumn: Optional[str] = None
   lookupLabelColumn: Optional[str] = None


class DataSpec(BaseModel):
   tables: List[TableSpec]
   relationships: Optional[List[RelationshipSpec]] = []


# --- Security Layer V3 (Entity-Action based) ---

class RoleSpec(BaseModel):
   name: str
   displayName: Optional[str] = None


class EntityPermission(BaseModel):
   role: str
   entity: str
   actions: Dict[str, bool]  # create, read, update, delete


class SecuritySpecV3(BaseModel):
   roles: List[RoleSpec]
   permissions: List[EntityPermission]


# --- Backend Configuration (V3 only) ---

class AuthConfig(BaseModel):
   provider: Literal["jwt", "basic", "none"] = "jwt"


class BackendSettings(BaseModel):
   generateREST: bool = True
   generateGraphQL: bool = False
   generateSwagger: bool = True


class BackendConfig(BaseModel):
   generator: Literal["amplication"] = "amplication"
   settings: BackendSettings = BackendSettings()
   auth: AuthConfig = AuthConfig()


# --- UI Blocks System ---

class FilterSpec(BaseModel):
   field: str
   operator: Literal["eq", "neq", "gt", "gte", "lt", "lte", "like", "in", "is_null", "is_not_null"]
   value: Any


class OrderSpec(BaseModel):
   field: str
   direction: Literal["asc", "desc"] = "asc"


class DataSourceSpec(BaseModel):
   entity: str  # V3 uses "entity" instead of "table"
   filters: Optional[List[FilterSpec]] = []
   orderBy: Optional[List[OrderSpec]] = []
   limit: Optional[int] = None
   include: Optional[List[str]] = []  # Relations to include
   realtime: Optional[bool] = False


class ActionConfig(BaseModel):
   trigger: str  # click, submit, change, cardClick, cardMove, etc.
   action: str   # navigate, openModal, closeModal, createRecord, updateRecord, deleteRecord, apiCall, etc.
   config: Optional[Dict[str, Any]] = {}
   condition: Optional[str] = None


class VisibilityRule(BaseModel):
   condition: str  # Expression like "{{$user.role}} === 'admin'"


# --- Block Specifications ---

class BlockSpec(BaseModel):
   id: str
   type: str  # TABLE, FORM, KANBAN, CALENDAR, CHART, STAT_CARD, etc.
   dataSource: Optional[DataSourceSpec] = None
   props: Dict[str, Any] = {}
   actions: Optional[List[ActionConfig]] = []
   gridArea: Optional[str] = None  # CSS grid placement
   className: Optional[str] = None
   visibility: Optional[VisibilityRule] = None
   children: Optional[List["BlockSpec"]] = []


# --- Layout System ---

class LayoutConfig(BaseModel):
   type: Literal["single", "split", "grid", "tabs"] = "single"
   config: Optional[Dict[str, Any]] = {}


class TabConfig(BaseModel):
   id: str
   label: str
   icon: Optional[str] = None


# --- Page & Modal Definitions ---

class PageSpec(BaseModel):
   id: str
   route: str
   title: str
   icon: Optional[str] = None
   layout: Optional[LayoutConfig] = None
   blocks: List[BlockSpec] = []
   variables: Optional[Dict[str, Any]] = {}  # Page-level state


class ModalSpec(BaseModel):
   id: str
   title: str
   size: Literal["small", "medium", "large", "fullscreen"] = "medium"
   blocks: List[BlockSpec] = []


class NavItem(BaseModel):
   name: str
   label: str
   icon: Optional[str] = None
   route: Optional[str] = None
   children: Optional[List["NavItem"]] = None


class GlobalAction(BaseModel):
   id: str
   label: str
   icon: Optional[str] = None
   action: str
   config: Dict[str, Any] = {}


# --- Theme ---

class ThemeSpec(BaseModel):
   primaryColor: Optional[str] = "#6366f1"
   mode: Optional[Literal["light", "dark"]] = "dark"
   fontFamily: Optional[str] = None


# --- App Info ---

class AppInfo(BaseModel):
   name: str
   slug: str
   description: Optional[str] = None
   theme: Optional[ThemeSpec] = None


# --- UI Spec V3 ---

class UISpecV3(BaseModel):
   navigation: List[NavItem] = []
   pages: List[PageSpec] = []
   modals: Optional[List[ModalSpec]] = []
   globalActions: Optional[List[GlobalAction]] = []


# --- Blueprint V3 (Main Schema) ---

class BlueprintV3(BaseModel):
   version: Literal[3] = 3
   app: AppInfo
   backend: BackendConfig = BackendConfig()
   data: DataSpec
   security: SecuritySpecV3
   ui: UISpecV3


# ============================================================================
# BLUEPRINT V2 SCHEMA (Legacy - for backwards compatibility)
# ============================================================================

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


class SecuritySpecV2(BaseModel):
   roles: List[str]
   permissions: List[PermissionRule]
   rowFilters: Optional[List[RowFilterRule]] = []


class DataSourceSpecV2(BaseModel):
   table: str  # V2 uses "table"
   filters: Optional[List[FilterSpec]] = []
   orderBy: Optional[List[OrderSpec]] = []
   limit: Optional[int] = None
   include: Optional[List[str]] = []
   realtime: Optional[bool] = False


class BlockSpecV2(BaseModel):
   id: str
   type: str
   dataSource: Optional[DataSourceSpecV2] = None
   props: Dict[str, Any] = {}
   actions: Optional[List[ActionConfig]] = []
   gridArea: Optional[str] = None
   className: Optional[str] = None
   visibility: Optional[VisibilityRule] = None
   children: Optional[List["BlockSpecV2"]] = []


class PageSpecV2(BaseModel):
   id: str
   route: str
   title: str
   icon: Optional[str] = None
   layout: Optional[LayoutConfig] = None
   blocks: List[BlockSpecV2] = []
   variables: Optional[Dict[str, Any]] = {}


class ModalSpecV2(BaseModel):
   id: str
   title: str
   size: Literal["small", "medium", "large", "fullscreen"] = "medium"
   blocks: List[BlockSpecV2] = []


class UISpecV2(BaseModel):
   navigation: List[NavItem] = []
   pages: List[PageSpecV2] = []
   modals: Optional[List[ModalSpecV2]] = []
   globalActions: Optional[List[GlobalAction]] = []


class TableSpecV2(BaseModel):
   name: str  # snake_case for V2
   primaryKey: str = "id"
   columns: List[ColumnSpec]


class RelationshipSpecV2(BaseModel):
   type: Literal["many_to_one", "one_to_many"]
   fromTable: str
   fromColumn: str
   toTable: str
   toColumn: str
   lookupLabelColumn: Optional[str] = None


class DataSpecV2(BaseModel):
   tables: List[TableSpecV2]
   relationships: Optional[List[RelationshipSpecV2]] = []


class BlueprintV2(BaseModel):
   version: Literal[2] = 2
   app: AppInfo
   data: DataSpecV2
   security: SecuritySpecV2
   ui: UISpecV2


# ============================================================================
# Union type for all Blueprint versions
# ============================================================================

Blueprint = Union[BlueprintV3, BlueprintV2]


# ============================================================================
# Response schemas
# ============================================================================

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
