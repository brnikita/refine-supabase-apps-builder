"use client";

import { useState } from "react";
import { BlockSpec, LayoutConfig } from "@/types/blueprint";
import { BlockRenderer } from "./BlockRenderer";

interface LayoutRendererProps {
   layout?: LayoutConfig;
   blocks: BlockSpec[];
   data: Record<string, any[]>;
   context?: {
      pageVariables?: Record<string, any>;
      selectedRecord?: any;
      user?: any;
   };
   onAction?: (action: string, config: any, context?: any) => void;
   onCreate?: (table: string, data: any) => Promise<any>;
   onUpdate?: (table: string, id: string, data: any) => Promise<any>;
   onDelete?: (table: string, id: string) => Promise<void>;
}

export function LayoutRenderer({
   layout,
   blocks,
   data,
   context = {},
   onAction,
   onCreate,
   onUpdate,
   onDelete,
}: LayoutRendererProps) {
   const [activeTab, setActiveTab] = useState(0);

   const layoutType = layout?.type || "single";
   const config = layout?.config || {};

   const renderBlocks = (blocksToRender: BlockSpec[]) => {
      return blocksToRender.map((block) => (
         <BlockRenderer
            key={block.id}
            block={block}
            data={data}
            context={context}
            onAction={onAction}
            onCreate={onCreate}
            onUpdate={onUpdate}
            onDelete={onDelete}
         />
      ));
   };

   switch (layoutType) {
      case "single":
         return (
            <div
               className="space-y-6"
               style={{
                  maxWidth: config.maxWidth || "100%",
                  padding: config.padding || "0",
               }}
            >
               {renderBlocks(blocks)}
            </div>
         );

      case "grid":
         const columns = config.columns || 4;
         const gap = config.gap || "16px";

         return (
            <div
               className="grid"
               style={{
                  gridTemplateColumns: `repeat(${columns}, minmax(0, 1fr))`,
                  gap,
               }}
            >
               {renderBlocks(blocks)}
            </div>
         );

      case "split":
         const sizes = config.sizes || [50, 50];
         const direction = config.direction || "horizontal";
         const isHorizontal = direction === "horizontal";

         // Split blocks into left/right or top/bottom
         const midpoint = Math.ceil(blocks.length / 2);
         const firstHalf = blocks.slice(0, midpoint);
         const secondHalf = blocks.slice(midpoint);

         return (
            <div
               className={`flex ${isHorizontal ? "flex-row" : "flex-col"} gap-4`}
               style={{ height: isHorizontal ? "100%" : "auto" }}
            >
               <div
                  className="overflow-auto"
                  style={{
                     [isHorizontal ? "width" : "height"]: `${sizes[0]}%`,
                  }}
               >
                  <div className="space-y-4">{renderBlocks(firstHalf)}</div>
               </div>
               <div
                  className="overflow-auto"
                  style={{
                     [isHorizontal ? "width" : "height"]: `${sizes[1]}%`,
                  }}
               >
                  <div className="space-y-4">{renderBlocks(secondHalf)}</div>
               </div>
            </div>
         );

      case "tabs":
         const tabs = config.tabs || blocks.map((b, i) => ({ id: b.id, label: `Tab ${i + 1}` }));

         return (
            <div>
               {/* Tab headers */}
               <div
                  className={`flex ${
                     config.position === "left" ? "flex-col w-48" : "flex-row"
                  } ${
                     config.position === "bottom" ? "order-2" : ""
                  } border-b border-white/10 mb-4`}
               >
                  {tabs.map((tab: { id: string; label: string; icon?: string }, index: number) => (
                     <button
                        key={tab.id}
                        onClick={() => setActiveTab(index)}
                        className={`px-4 py-2 text-sm font-medium transition-colors ${
                           activeTab === index
                              ? "text-primary-400 border-b-2 border-primary-500 -mb-px"
                              : "text-white/60 hover:text-white"
                        }`}
                     >
                        {tab.label}
                     </button>
                  ))}
               </div>

               {/* Tab content */}
               <div className="space-y-4">
                  {blocks[activeTab] && (
                     <BlockRenderer
                        block={blocks[activeTab]}
                        data={data}
                        context={context}
                        onAction={onAction}
                        onCreate={onCreate}
                        onUpdate={onUpdate}
                        onDelete={onDelete}
                     />
                  )}
               </div>
            </div>
         );

      default:
         return <div className="space-y-6">{renderBlocks(blocks)}</div>;
   }
}

