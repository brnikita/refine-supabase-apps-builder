"use client";

import { useState, useMemo } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Plus, MoreHorizontal, GripVertical, User, Calendar } from "lucide-react";
import { BlockComponentProps } from "./index";
import { KanbanProps } from "@/types/blueprint";

interface KanbanCard {
   id: string;
   [key: string]: any;
}

export function KanbanBlock({
   block,
   data,
   loading,
   onUpdate,
   onAction,
}: BlockComponentProps) {
   const props = block.props as KanbanProps;
   const [draggedCard, setDraggedCard] = useState<KanbanCard | null>(null);
   const [dragOverColumn, setDragOverColumn] = useState<string | null>(null);

   // Group data by the groupByField
   const groupedData = useMemo(() => {
      const groups: Record<string, KanbanCard[]> = {};

      // Initialize all columns
      props.columns.forEach((col) => {
         groups[col.value] = [];
      });

      // Group data
      data?.forEach((item) => {
         const columnValue = item[props.groupByField] || props.columns[0]?.value;
         if (groups[columnValue]) {
            groups[columnValue].push(item);
         }
      });

      return groups;
   }, [data, props.groupByField, props.columns]);

   const handleDragStart = (e: React.DragEvent, card: KanbanCard) => {
      setDraggedCard(card);
      e.dataTransfer.effectAllowed = "move";
      // Add some visual feedback
      (e.target as HTMLElement).style.opacity = "0.5";
   };

   const handleDragEnd = (e: React.DragEvent) => {
      (e.target as HTMLElement).style.opacity = "1";
      setDraggedCard(null);
      setDragOverColumn(null);
   };

   const handleDragOver = (e: React.DragEvent, columnValue: string) => {
      e.preventDefault();
      e.dataTransfer.dropEffect = "move";
      setDragOverColumn(columnValue);
   };

   const handleDragLeave = () => {
      setDragOverColumn(null);
   };

   const handleDrop = async (e: React.DragEvent, columnValue: string) => {
      e.preventDefault();
      setDragOverColumn(null);

      if (draggedCard && draggedCard[props.groupByField] !== columnValue) {
         // Update the card's status
         await onUpdate?.(draggedCard.id, { [props.groupByField]: columnValue });

         // Trigger action
         onAction?.("cardMove", {
            card: draggedCard,
            fromColumn: draggedCard[props.groupByField],
            toColumn: columnValue,
         });
      }
   };

   const handleCardClick = (card: KanbanCard) => {
      onAction?.("cardClick", { card }, { selectedRecord: card });
   };

   const handleCreateClick = (columnValue: string) => {
      onAction?.("createClick", { column: columnValue, defaultValues: { [props.groupByField]: columnValue } });
   };

   const renderCard = (card: KanbanCard) => {
      const title = card[props.card.titleField];
      const description = props.card.descriptionField
         ? card[props.card.descriptionField]
         : null;
      const badge = props.card.badgeField ? card[props.card.badgeField] : null;
      const badgeColor = badge && props.card.badgeColors?.[badge];

      return (
         <div
            key={card.id}
            draggable={props.allowDragDrop !== false}
            onDragStart={(e) => handleDragStart(e, card)}
            onDragEnd={handleDragEnd}
            onClick={() => handleCardClick(card)}
            className="bg-white/5 border border-white/10 rounded-lg p-3 cursor-pointer hover:bg-white/10 hover:border-white/20 transition-all group"
         >
            {/* Drag handle */}
            {props.allowDragDrop !== false && (
               <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                  <GripVertical className="w-4 h-4 text-white/40" />
               </div>
            )}

            {/* Badge */}
            {badge && (
               <Badge
                  className="mb-2"
                  style={badgeColor ? { backgroundColor: badgeColor, color: "#fff" } : undefined}
               >
                  {String(badge).replace(/_/g, " ")}
               </Badge>
            )}

            {/* Title */}
            <h4 className="font-medium text-white mb-1 pr-6">{title}</h4>

            {/* Description */}
            {description && (
               <p className="text-sm text-white/60 line-clamp-2 mb-2">{description}</p>
            )}

            {/* Meta fields */}
            {props.card.metaFields && props.card.metaFields.length > 0 && (
               <div className="flex items-center gap-3 mt-3 pt-2 border-t border-white/10">
                  {props.card.metaFields.map((field) => {
                     const value = card[field];
                     if (!value) return null;

                     // Render based on field name heuristics
                     if (field.includes("date") || field.includes("_at")) {
                        return (
                           <div key={field} className="flex items-center gap-1 text-xs text-white/50">
                              <Calendar className="w-3 h-3" />
                              {new Date(value).toLocaleDateString()}
                           </div>
                        );
                     }

                     if (field.includes("assignee") || field.includes("user") || field.includes("owner")) {
                        return (
                           <div key={field} className="flex items-center gap-1 text-xs text-white/50">
                              <User className="w-3 h-3" />
                              {typeof value === "object" ? value.name || value.email : value}
                           </div>
                        );
                     }

                     return (
                        <span key={field} className="text-xs text-white/50">
                           {String(value)}
                        </span>
                     );
                  })}
               </div>
            )}
         </div>
      );
   };

   if (loading) {
      return (
         <div className="flex gap-4 overflow-x-auto pb-4">
            {props.columns.map((col) => (
               <div key={col.value} className="flex-shrink-0 w-72">
                  <Card className="p-4 h-96 animate-pulse">
                     <div className="h-6 w-24 bg-white/10 rounded mb-4" />
                     <div className="space-y-3">
                        <div className="h-24 bg-white/5 rounded" />
                        <div className="h-24 bg-white/5 rounded" />
                     </div>
                  </Card>
               </div>
            ))}
         </div>
      );
   }

   return (
      <div className="flex gap-4 overflow-x-auto pb-4 -mx-2 px-2">
         {props.columns.map((column) => {
            const cards = groupedData[column.value] || [];
            const isOver = dragOverColumn === column.value;
            const isAtLimit = column.limit && cards.length >= column.limit;

            return (
               <div
                  key={column.value}
                  className="flex-shrink-0 w-72"
                  onDragOver={(e) => handleDragOver(e, column.value)}
                  onDragLeave={handleDragLeave}
                  onDrop={(e) => handleDrop(e, column.value)}
               >
                  <Card
                     className={`p-3 min-h-[500px] transition-all ${
                        isOver ? "ring-2 ring-primary-500 bg-primary-500/5" : ""
                     }`}
                  >
                     {/* Column Header */}
                     <div className="flex items-center justify-between mb-3 pb-2 border-b border-white/10">
                        <div className="flex items-center gap-2">
                           <div
                              className="w-3 h-3 rounded-full"
                              style={{ backgroundColor: column.color || "#6366f1" }}
                           />
                           <h3 className="font-medium text-white">{column.label}</h3>
                           <span className="text-sm text-white/40">
                              {cards.length}
                              {column.limit && `/${column.limit}`}
                           </span>
                        </div>
                        <button className="p-1 rounded hover:bg-white/10 text-white/40 hover:text-white transition-colors">
                           <MoreHorizontal className="w-4 h-4" />
                        </button>
                     </div>

                     {/* Cards */}
                     <div className="space-y-2">
                        {cards.map(renderCard)}

                        {/* Empty state */}
                        {cards.length === 0 && (
                           <div className="py-8 text-center text-white/30 text-sm">
                              No items
                           </div>
                        )}

                        {/* Add button */}
                        {props.allowCreate && !isAtLimit && (
                           <Button
                              variant="ghost"
                              className="w-full justify-start text-white/40 hover:text-white"
                              onClick={() => handleCreateClick(column.value)}
                           >
                              <Plus className="w-4 h-4 mr-2" />
                              Add item
                           </Button>
                        )}

                        {/* Limit warning */}
                        {isAtLimit && (
                           <p className="text-xs text-center text-yellow-500/60 py-2">
                              Column limit reached
                           </p>
                        )}
                     </div>
                  </Card>
               </div>
            );
         })}
      </div>
   );
}

