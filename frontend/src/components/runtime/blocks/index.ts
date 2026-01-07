// Block Component Registry
// Maps block type strings to React components

import { ComponentType } from 'react';
import { BlockSpec } from '@/types/blueprint';

// Import block components
import { TableBlock } from './TableBlock';
import { FormBlock } from './FormBlock';
import { DetailBlock } from './DetailBlock';
import { StatCardBlock } from './StatCardBlock';
import { ChartBlock } from './ChartBlock';
import { KanbanBlock } from './KanbanBlock';
import { CalendarBlock } from './CalendarBlock';
import { TimelineBlock } from './TimelineBlock';
import { ChatBlock } from './ChatBlock';
import { GalleryBlock } from './GalleryBlock';
import { TreeBlock } from './TreeBlock';
import { UnknownBlock } from './UnknownBlock';

// Block component props interface
export interface BlockComponentProps {
   block: BlockSpec;
   data: any[];
   loading?: boolean;
   error?: Error | null;
   onCreate?: (data: any) => Promise<any>;
   onUpdate?: (id: string, data: any) => Promise<any>;
   onDelete?: (id: string) => Promise<void>;
   onRefresh?: () => void;
   onAction?: (action: string, config: any, context?: any) => void;
   context?: {
      pageVariables?: Record<string, any>;
      selectedRecord?: any;
      user?: any;
   };
   // V3: Function to fetch data from API
   fetchData?: (options?: {
      page?: number;
      pageSize?: number;
      sort?: { field: string; order: 'asc' | 'desc' };
      filters?: Array<{ field: string; value: any }>;
   }) => Promise<{ data: any[]; total: number }>;
}

// Component registry type
export type BlockComponentType = ComponentType<BlockComponentProps>;

// The registry mapping block types to components (all lowercase)
const componentRegistry: Record<string, BlockComponentType> = {
   // Core blocks
   'table': TableBlock,
   'form': FormBlock,
   'detail': DetailBlock,
   'stat-card': StatCardBlock,
   'statcard': StatCardBlock,
   'chart': ChartBlock,
   
   // Specialized blocks
   'kanban': KanbanBlock,
   'calendar': CalendarBlock,
   'timeline': TimelineBlock,
   'chat': ChatBlock,
   'gallery': GalleryBlock,
   'tree': TreeBlock,
   
   // Fallback
   'unknown': UnknownBlock,
};

// Normalize block type to lowercase and handle variations
function normalizeBlockType(type: string): string {
   // Convert to lowercase
   let normalized = type.toLowerCase();
   
   // Handle common variations
   const aliases: Record<string, string> = {
      'stat-card': 'stat-card',
      'statcard': 'stat-card',
      'stat_card': 'stat-card',
      'data-table': 'table',
      'datatable': 'table',
      'data_table': 'table',
      'list': 'table',
      'kanban-board': 'kanban',
      'kanbanboard': 'kanban',
      'kanban_board': 'kanban',
      'board': 'kanban',
      'tree-view': 'tree',
      'treeview': 'tree',
      'tree_view': 'tree',
      'file-list': 'tree',
      'filelist': 'tree',
      'file_list': 'tree',
   };
   
   return aliases[normalized] || normalized;
}

// Get component for a block type (case-insensitive)
export function getBlockComponent(type: string): BlockComponentType {
   const normalizedType = normalizeBlockType(type);
   return componentRegistry[normalizedType] || UnknownBlock;
}

// Check if a block type is registered
export function isBlockTypeRegistered(type: string): boolean {
   const normalizedType = normalizeBlockType(type);
   return normalizedType in componentRegistry;
}

// Register a new block component (for extensibility)
export function registerBlockComponent(type: string, component: BlockComponentType): void {
   componentRegistry[type.toLowerCase()] = component;
}

// Export the registry for inspection
export { componentRegistry };
