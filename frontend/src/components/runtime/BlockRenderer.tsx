"use client";

import { useMemo } from "react";
import { BlockSpec, DataSourceSpec, getEntityFromDataSource } from "@/types/blueprint";
import { getBlockComponent, BlockComponentProps } from "./blocks";

interface BlockRendererProps {
   block: BlockSpec;
   data: Record<string, any[]>;
   context?: {
      pageVariables?: Record<string, any>;
      selectedRecord?: any;
      user?: any;
   };
   onAction?: (action: string, config: any, context?: any) => void;
   onCreate?: (entity: string, data: any) => Promise<any>;
   onUpdate?: (entity: string, id: string, data: any) => Promise<any>;
   onDelete?: (entity: string, id: string) => Promise<void>;
   fetchData?: (entity: string, options?: any) => Promise<{ data: any[]; total: number }>;
}

export function BlockRenderer({
   block,
   data,
   context = {},
   onAction,
   onCreate,
   onUpdate,
   onDelete,
   fetchData,
}: BlockRendererProps) {
   // Get the component for this block type
   const Component = getBlockComponent(block.type);

   // Get entity name from data source (handles both V2 "table" and V3 "entity")
   const entityName = getEntityFromDataSource(block.dataSource);

   // Get data for this block's data source
   const blockData = useMemo(() => {
      if (!entityName) return [];
      const tableData = data[entityName] || [];

      // Apply filters (simple implementation)
      let filtered = tableData;
      const dataSource = block.dataSource;
      
      if (dataSource?.filters && dataSource.filters.length > 0) {
         filtered = tableData.filter((item) => {
            return dataSource.filters!.every((filter) => {
               const value = item[filter.field];
               const filterValue = resolveTemplateValue(filter.value, context);

               switch (filter.operator) {
                  case "eq":
                     return value === filterValue;
                  case "neq":
                     return value !== filterValue;
                  case "gt":
                     return value > filterValue;
                  case "gte":
                     return value >= filterValue;
                  case "lt":
                     return value < filterValue;
                  case "lte":
                     return value <= filterValue;
                  case "like":
                     return String(value).includes(String(filterValue));
                  case "in":
                     return Array.isArray(filterValue) && filterValue.includes(value);
                  case "is_null":
                     return value === null || value === undefined;
                  case "is_not_null":
                     return value !== null && value !== undefined;
                  default:
                     return true;
               }
            });
         });
      }

      // Apply ordering
      if (dataSource?.orderBy && dataSource.orderBy.length > 0) {
         filtered = [...filtered].sort((a, b) => {
            for (const order of dataSource.orderBy!) {
               const aVal = a[order.field];
               const bVal = b[order.field];
               if (aVal === bVal) continue;
               if (aVal === null || aVal === undefined) return 1;
               if (bVal === null || bVal === undefined) return -1;
               const comparison = aVal < bVal ? -1 : 1;
               return order.direction === "asc" ? comparison : -comparison;
            }
            return 0;
         });
      }

      // Apply limit
      if (dataSource?.limit) {
         filtered = filtered.slice(0, dataSource.limit);
      }

      return filtered;
   }, [block.dataSource, data, context, entityName]);

   // Check visibility
   if (block.visibility) {
      const isVisible = evaluateCondition(block.visibility.condition, context);
      if (!isVisible) return null;
   }

   // Wrap CRUD operations with entity name
   const handleCreate = entityName && onCreate
      ? async (data: any) => onCreate(entityName, data)
      : undefined;

   const handleUpdate = entityName && onUpdate
      ? async (id: string, data: any) => onUpdate(entityName, id, data)
      : undefined;

   const handleDelete = entityName && onDelete
      ? async (id: string) => onDelete(entityName, id)
      : undefined;

   // Wrap fetchData with entity name
   const handleFetchData = entityName && fetchData
      ? (options?: any) => fetchData(entityName, options)
      : undefined;

   // Handle actions from blocks
   const handleAction = (action: string, config: any, actionContext?: any) => {
      // Merge contexts
      const mergedContext = { ...context, ...actionContext };

      // Check if block has defined actions for this trigger
      const blockAction = block.actions?.find((a) => a.trigger === action);
      if (blockAction) {
         onAction?.(blockAction.action, { ...blockAction.config, ...config }, mergedContext);
      } else {
         onAction?.(action, config, mergedContext);
      }
   };

   // Build component props
   const componentProps: BlockComponentProps = {
      block,
      data: blockData,
      loading: false,
      error: null,
      onCreate: handleCreate,
      onUpdate: handleUpdate,
      onDelete: handleDelete,
      onRefresh: handleFetchData ? () => { handleFetchData(); } : () => {},
      onAction: handleAction,
      context,
      fetchData: handleFetchData,
   };

   // Apply grid area if specified
   const style: React.CSSProperties = {};
   if (block.gridArea) {
      style.gridArea = block.gridArea;
   }

   return (
      <div style={style} className={block.className}>
         <Component {...componentProps} />
      </div>
   );
}

// Helper to resolve template expressions like {{field}} or {{$user.id}}
function resolveTemplateValue(value: any, context: any): any {
   if (typeof value !== "string") return value;

   const templateRegex = /\{\{([^}]+)\}\}/g;
   let match;
   let result = value;

   while ((match = templateRegex.exec(value)) !== null) {
      const expression = match[1].trim();
      const resolved = evaluateExpression(expression, context);
      result = result.replace(match[0], String(resolved ?? ""));
   }

   return result;
}

// Evaluate simple expressions
function evaluateExpression(expression: string, context: any): any {
   // Handle special variables
   if (expression.startsWith("$user.")) {
      const path = expression.slice(6);
      return getNestedValue(context.user, path);
   }
   if (expression.startsWith("$page.")) {
      const path = expression.slice(6);
      return getNestedValue(context.pageVariables, path);
   }
   if (expression.startsWith("$route.")) {
      const path = expression.slice(7);
      return getNestedValue(context.routeParams, path);
   }
   if (expression === "$now") {
      return new Date().toISOString();
   }

   // Handle record field access
   if (context.selectedRecord) {
      return getNestedValue(context.selectedRecord, expression);
   }

   return null;
}

// Get nested object value by path
function getNestedValue(obj: any, path: string): any {
   if (!obj) return null;
   return path.split(".").reduce((acc, part) => acc?.[part], obj);
}

// Evaluate visibility conditions
function evaluateCondition(condition: string, context: any): boolean {
   try {
      // Simple condition evaluation
      // In production, use a proper expression parser
      const resolved = resolveTemplateValue(condition, context);

      // Handle simple comparisons
      if (resolved.includes("===")) {
         const [left, right] = resolved.split("===").map((s: string) => s.trim());
         return left === right;
      }
      if (resolved.includes("!==")) {
         const [left, right] = resolved.split("!==").map((s: string) => s.trim());
         return left !== right;
      }

      return Boolean(resolved);
   } catch {
      return true;
   }
}
