from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional, List, Dict, Any, Literal, Union
from app.models.blueprint import ValidationStatus


# ============================================================================
# BLUEPRINT V2 SCHEMA - Dynamic UI Blocks System
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


class DataSpec(BaseModel):
   tables: List[TableSpec]
   relationships: Optional[List[RelationshipSpec]] = []


# --- Security Layer ---

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


class SecuritySpec(BaseModel):
   roles: List[str]
   permissions: List[PermissionRule]
   rowFilters: Optional[List[RowFilterRule]] = []


# --- UI Blocks System (V2) ---

class FilterSpec(BaseModel):
   field: str
   operator: Literal["eq", "neq", "gt", "gte", "lt", "lte", "like", "in", "is_null", "is_not_null"]
   value: Any


class OrderSpec(BaseModel):
   field: str
   direction: Literal["asc", "desc"] = "asc"


class DataSourceSpec(BaseModel):
   table: str
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
   type: str  # table, form, kanban, calendar, chart, stat-card, etc.
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


# --- UI Spec V2 ---

class UISpecV2(BaseModel):
   navigation: List[NavItem] = []
   pages: List[PageSpec] = []
   modals: Optional[List[ModalSpec]] = []
   globalActions: Optional[List[GlobalAction]] = []


# --- Blueprint V2 (Main Schema) ---

class BlueprintV2(BaseModel):
   version: int = 2
   app: AppInfo
   data: DataSpec
   security: SecuritySpec
   ui: UISpecV2


# ============================================================================
# Alias for backwards compatibility (Blueprint = BlueprintV2)
# ============================================================================

Blueprint = BlueprintV2


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
