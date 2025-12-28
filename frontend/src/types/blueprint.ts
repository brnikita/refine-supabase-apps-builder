// ============================================================================
// BLUEPRINT V2 TYPES - Dynamic UI Blocks System
// ============================================================================

// --- Data Layer ---

export interface ColumnSpec {
   name: string;
   type: 'uuid' | 'text' | 'int' | 'float' | 'bool' | 'date' | 'timestamptz' | 'jsonb';
   required?: boolean;
   default?: any;
   unique?: boolean;
   indexed?: boolean;
}

export interface TableSpec {
   name: string;
   primaryKey?: string;
   columns: ColumnSpec[];
}

export interface RelationshipSpec {
   type: 'many_to_one' | 'one_to_many';
   fromTable: string;
   fromColumn: string;
   toTable: string;
   toColumn: string;
   lookupLabelColumn?: string;
}

export interface DataSpec {
   tables: TableSpec[];
   relationships?: RelationshipSpec[];
}

// --- Security Layer ---

export interface PermissionRule {
   role: string;
   resource: string;
   actions: Record<string, boolean>;
}

export interface RowFilterRule {
   role: string;
   resource: string;
   filter: any;
}

export interface SecuritySpec {
   roles: string[];
   permissions: PermissionRule[];
   rowFilters?: RowFilterRule[];
}

// --- UI Blocks System ---

export interface FilterSpec {
   field: string;
   operator: 'eq' | 'neq' | 'gt' | 'gte' | 'lt' | 'lte' | 'like' | 'in' | 'is_null' | 'is_not_null';
   value: any;
}

export interface OrderSpec {
   field: string;
   direction: 'asc' | 'desc';
}

export interface DataSourceSpec {
   table: string;
   filters?: FilterSpec[];
   orderBy?: OrderSpec[];
   limit?: number;
   include?: string[];
   realtime?: boolean;
}

export interface ActionConfig {
   trigger: string;
   action: string;
   config?: Record<string, any>;
   condition?: string;
}

export interface VisibilityRule {
   condition: string;
}

// --- Block Types ---

export type BlockType =
   | 'table'
   | 'form'
   | 'detail'
   | 'stat-card'
   | 'chart'
   | 'kanban'
   | 'calendar'
   | 'timeline'
   | 'chat'
   | 'gallery'
   | 'tree'
   | 'file-list'
   | 'container'
   | 'tabs'
   | 'split-view'
   | 'button'
   | 'search'
   | 'filter-bar'
   | 'markdown';

export interface BlockSpec {
   id: string;
   type: BlockType | string;
   dataSource?: DataSourceSpec;
   props: Record<string, any>;
   actions?: ActionConfig[];
   gridArea?: string;
   className?: string;
   visibility?: VisibilityRule;
   children?: BlockSpec[];
}

// --- Block Props Types ---

export interface TableColumnDef {
   field: string;
   label: string;
   type?: 'text' | 'number' | 'date' | 'datetime' | 'badge' | 'boolean' | 'image' | 'link';
   sortable?: boolean;
   width?: string;
}

export interface TableProps {
   columns: TableColumnDef[];
   allowSearch?: boolean;
   allowFilter?: boolean;
   allowSort?: boolean;
   allowSelect?: boolean;
   allowExport?: boolean;
   pagination?: { pageSize: number };
   rowActions?: ('view' | 'edit' | 'delete' | ActionConfig)[];
   emptyMessage?: string;
}

export interface FormFieldDef {
   name: string;
   label: string;
   type: 'text' | 'textarea' | 'number' | 'select' | 'checkbox' | 'date' | 'datetime' | 'relation' | 'file' | 'color' | 'email' | 'password' | 'url';
   required?: boolean;
   options?: string[] | { value: string; label: string }[];
   placeholder?: string;
   defaultValue?: any;
   table?: string; // For relation fields
}

export interface FormProps {
   mode: 'create' | 'edit';
   fields: FormFieldDef[];
   submitLabel?: string;
   cancelLabel?: string;
}

export interface DetailFieldDef {
   name: string;
   label: string;
   type?: 'text' | 'date' | 'datetime' | 'badge' | 'boolean' | 'image' | 'link';
}

export interface DetailProps {
   fields: DetailFieldDef[];
   layout?: 'vertical' | 'horizontal' | 'grid';
}

export interface StatCardProps {
   title: string;
   value?: string | number;
   valueField?: string;
   icon?: string;
   trend?: number;
   trendDirection?: 'up' | 'down';
   color?: string;
   query?: string;
}

export interface ChartProps {
   chartType: 'bar' | 'line' | 'pie' | 'donut' | 'area' | 'scatter';
   xField?: string;
   yField?: string;
   groupField?: string;
   aggregation?: 'count' | 'sum' | 'avg' | 'min' | 'max';
   colors?: string[];
   showLegend?: boolean;
   showGrid?: boolean;
   animate?: boolean;
}

export interface KanbanColumnDef {
   value: string;
   label: string;
   color?: string;
   limit?: number;
}

export interface KanbanCardConfig {
   titleField: string;
   descriptionField?: string;
   metaFields?: string[];
   badgeField?: string;
   badgeColors?: Record<string, string>;
   avatarField?: string;
}

export interface KanbanProps {
   groupByField: string;
   columns: KanbanColumnDef[];
   card: KanbanCardConfig;
   allowDragDrop?: boolean;
   allowCreate?: boolean;
   allowCollapse?: boolean;
}

export interface CalendarProps {
   startField: string;
   endField: string;
   titleField: string;
   colorField?: string;
   colors?: Record<string, string>;
   views?: ('month' | 'week' | 'day' | 'agenda')[];
   defaultView?: string;
   allowCreate?: boolean;
   allowDrag?: boolean;
   allowResize?: boolean;
   minTime?: string;
   maxTime?: string;
}

export interface TimelineProps {
   dateField: string;
   titleField: string;
   descriptionField?: string;
   groupBy?: 'day' | 'week' | 'month';
   showTime?: boolean;
   iconField?: string;
   colorField?: string;
}

export interface ChatProps {
   messageField: string;
   senderNameField: string;
   senderAvatarField?: string;
   timestampField: string;
   allowReply?: boolean;
   allowReactions?: boolean;
   allowAttachments?: boolean;
   allowEdit?: boolean;
   allowDelete?: boolean;
   realtime?: boolean;
}

export interface GalleryProps {
   imageField: string;
   titleField?: string;
   descriptionField?: string;
   columns?: number;
   aspectRatio?: '1:1' | '16:9' | '4:3' | '3:2';
   allowLightbox?: boolean;
}

export interface TreeProps {
   titleField: string;
   parentField?: string;
   iconField?: string;
   expandable?: boolean;
   selectable?: boolean;
}

// --- Layout System ---

export interface LayoutConfig {
   type: 'single' | 'split' | 'grid' | 'tabs';
   config?: {
      // For split
      direction?: 'horizontal' | 'vertical';
      sizes?: number[];
      resizable?: boolean;
      // For grid
      columns?: number;
      rows?: string;
      gap?: string;
      // For tabs
      position?: 'top' | 'left' | 'bottom';
      tabs?: { id: string; label: string; icon?: string }[];
      // For single
      maxWidth?: string;
      padding?: string;
   };
}

// --- Page & Modal Definitions ---

export interface PageSpec {
   id: string;
   route: string;
   title: string;
   icon?: string;
   layout?: LayoutConfig;
   blocks: BlockSpec[];
   variables?: Record<string, any>;
}

export interface ModalSpec {
   id: string;
   title: string;
   size?: 'small' | 'medium' | 'large' | 'fullscreen';
   blocks: BlockSpec[];
}

export interface NavItem {
   name: string;
   label: string;
   icon?: string;
   route?: string;
   children?: NavItem[];
}

export interface GlobalAction {
   id: string;
   label: string;
   icon?: string;
   action: string;
   config: Record<string, any>;
}

// --- Theme ---

export interface ThemeSpec {
   primaryColor?: string;
   mode?: 'light' | 'dark';
   fontFamily?: string;
}

// --- App Info ---

export interface AppInfo {
   name: string;
   slug: string;
   description?: string;
   theme?: ThemeSpec;
}

// --- UI Spec ---

export interface UISpec {
   navigation: NavItem[];
   pages: PageSpec[];
   modals?: ModalSpec[];
   globalActions?: GlobalAction[];
}

// --- Blueprint V2 (Main Type) ---

export interface BlueprintV2 {
   version: 2;
   app: AppInfo;
   data: DataSpec;
   security: SecuritySpec;
   ui: UISpec;
}

// --- Legacy V1 Support ---

export interface ResourceSpec {
   name: string;
   table: string;
   label: string;
   views?: Record<string, boolean>;
   list?: { columns: string[] };
   forms?: {
      createFields?: { name: string; widget?: string; label?: string; options?: any[] }[];
      editFields?: { name: string; widget?: string; label?: string; options?: any[] }[];
   };
}

export interface UISpecV1 {
   navigation: NavItem[];
   resources: ResourceSpec[];
   pages?: any[];
}

export interface BlueprintV1 {
   version: 1;
   app: AppInfo;
   data: DataSpec;
   security: SecuritySpec;
   ui: UISpecV1;
}

// Union type for both versions
export type Blueprint = BlueprintV1 | BlueprintV2;

// Type guard to check blueprint version
export function isBlueprintV2(blueprint: Blueprint): blueprint is BlueprintV2 {
   return blueprint.version === 2 && 'pages' in blueprint.ui;
}

export function isBlueprintV1(blueprint: Blueprint): blueprint is BlueprintV1 {
   return blueprint.version === 1 || 'resources' in blueprint.ui;
}

