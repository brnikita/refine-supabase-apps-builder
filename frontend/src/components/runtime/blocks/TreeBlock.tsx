"use client";

import { useState, useMemo } from "react";
import { Card } from "@/components/ui/card";
import {
   ChevronRight,
   ChevronDown,
   Folder,
   FolderOpen,
   File,
   Hash,
   Lock,
   User,
   Settings,
   Circle,
} from "lucide-react";
import { BlockComponentProps } from "./index";
import { TreeProps } from "@/types/blueprint";

interface TreeItem {
   id: string;
   [key: string]: any;
}

interface TreeNode extends TreeItem {
   children?: TreeNode[];
}

const iconMap: Record<string, any> = {
   folder: Folder,
   "folder-open": FolderOpen,
   file: File,
   hash: Hash,
   lock: Lock,
   user: User,
   settings: Settings,
   default: Circle,
};

export function TreeBlock({
   block,
   data,
   loading,
   onAction,
}: BlockComponentProps) {
   const props = block.props as TreeProps;
   const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set());
   const [selectedNode, setSelectedNode] = useState<string | null>(null);

   // Build tree structure from flat data
   const treeData = useMemo(() => {
      if (!data || data.length === 0) return [];

      // If no parentField, return flat list
      if (!props.parentField) {
         return data.map((item) => ({ ...item, children: [] }));
      }

      // Build tree from parent-child relationships
      const nodeMap = new Map<string, TreeNode>();
      const roots: TreeNode[] = [];

      // First pass: create all nodes
      data.forEach((item) => {
         nodeMap.set(item.id, { ...item, children: [] });
      });

      // Second pass: build tree structure
      data.forEach((item) => {
         const node = nodeMap.get(item.id)!;
         const parentId = item[props.parentField!];

         if (parentId && nodeMap.has(parentId)) {
            nodeMap.get(parentId)!.children!.push(node);
         } else {
            roots.push(node);
         }
      });

      return roots;
   }, [data, props.parentField]);

   const toggleExpand = (nodeId: string) => {
      setExpandedNodes((prev) => {
         const next = new Set(prev);
         if (next.has(nodeId)) {
            next.delete(nodeId);
         } else {
            next.add(nodeId);
         }
         return next;
      });
   };

   const handleNodeClick = (node: TreeNode) => {
      if (props.selectable !== false) {
         setSelectedNode(node.id);
      }
      onAction?.("itemClick", { item: node }, { selectedRecord: node });
   };

   const getNodeIcon = (node: TreeNode, isExpanded: boolean) => {
      if (props.iconField && node[props.iconField]) {
         const iconName = node[props.iconField];
         const Icon = iconMap[iconName.toLowerCase()] || iconMap.default;
         return Icon;
      }

      // Default icons based on whether node has children
      if (node.children && node.children.length > 0) {
         return isExpanded ? FolderOpen : Folder;
      }
      return File;
   };

   const renderNode = (node: TreeNode, depth: number = 0) => {
      const isExpanded = expandedNodes.has(node.id);
      const isSelected = selectedNode === node.id;
      const hasChildren = node.children && node.children.length > 0;
      const title = node[props.titleField] || node.id;
      const Icon = getNodeIcon(node, isExpanded);

      return (
         <div key={node.id}>
            <div
               className={`flex items-center gap-2 px-2 py-1.5 rounded-lg cursor-pointer transition-colors ${
                  isSelected
                     ? "bg-primary-500/20 text-primary-400"
                     : "text-white/80 hover:bg-white/10"
               }`}
               style={{ paddingLeft: `${depth * 16 + 8}px` }}
               onClick={() => handleNodeClick(node)}
            >
               {/* Expand/collapse button */}
               {props.expandable !== false && hasChildren ? (
                  <button
                     className="p-0.5 rounded hover:bg-white/10"
                     onClick={(e) => {
                        e.stopPropagation();
                        toggleExpand(node.id);
                     }}
                  >
                     {isExpanded ? (
                        <ChevronDown className="w-4 h-4 text-white/60" />
                     ) : (
                        <ChevronRight className="w-4 h-4 text-white/60" />
                     )}
                  </button>
               ) : (
                  <span className="w-5" />
               )}

               {/* Icon */}
               <Icon className="w-4 h-4 text-white/60" />

               {/* Title */}
               <span className="truncate">{title}</span>
            </div>

            {/* Children */}
            {props.expandable !== false && isExpanded && hasChildren && (
               <div>
                  {node.children!.map((child) => renderNode(child, depth + 1))}
               </div>
            )}
         </div>
      );
   };

   if (loading) {
      return (
         <Card className="p-4">
            <div className="space-y-2">
               {[1, 2, 3, 4, 5].map((i) => (
                  <div
                     key={i}
                     className="flex items-center gap-2 animate-pulse"
                     style={{ paddingLeft: `${(i % 3) * 16 + 8}px` }}
                  >
                     <div className="w-4 h-4 bg-white/10 rounded" />
                     <div className="w-4 h-4 bg-white/10 rounded" />
                     <div className="h-4 w-24 bg-white/10 rounded" />
                  </div>
               ))}
            </div>
         </Card>
      );
   }

   if (!data || data.length === 0) {
      return (
         <Card className="p-4">
            <div className="text-center py-8 text-white/40">
               <Folder className="w-12 h-12 mx-auto mb-3 opacity-50" />
               <p>No items</p>
            </div>
         </Card>
      );
   }

   return (
      <Card className="p-2">
         <div className="space-y-0.5">
            {treeData.map((node) => renderNode(node))}
         </div>
      </Card>
   );
}

