"use client";

import { useMemo } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
   Clock,
   Circle,
   CheckCircle,
   AlertCircle,
   FileText,
   MessageSquare,
   User,
   Calendar,
} from "lucide-react";
import { BlockComponentProps } from "./index";
import { TimelineProps } from "@/types/blueprint";

interface TimelineItem {
   id: string;
   [key: string]: any;
}

const iconMap: Record<string, any> = {
   default: Circle,
   check: CheckCircle,
   alert: AlertCircle,
   file: FileText,
   message: MessageSquare,
   user: User,
   calendar: Calendar,
};

export function TimelineBlock({
   block,
   data,
   loading,
   onAction,
}: BlockComponentProps) {
   const props = block.props as TimelineProps;

   // Group items by date
   const groupedItems = useMemo(() => {
      if (!data || data.length === 0) return new Map();

      const groups = new Map<string, TimelineItem[]>();

      const sortedData = [...data].sort((a, b) => {
         const dateA = new Date(a[props.dateField]);
         const dateB = new Date(b[props.dateField]);
         return dateB.getTime() - dateA.getTime(); // Most recent first
      });

      sortedData.forEach((item) => {
         const date = new Date(item[props.dateField]);
         let groupKey: string;

         switch (props.groupBy) {
            case "week":
               const weekStart = new Date(date);
               weekStart.setDate(date.getDate() - date.getDay());
               groupKey = weekStart.toLocaleDateString("en-US", {
                  month: "short",
                  day: "numeric",
               });
               break;
            case "month":
               groupKey = date.toLocaleDateString("en-US", {
                  month: "long",
                  year: "numeric",
               });
               break;
            default: // day
               groupKey = date.toLocaleDateString("en-US", {
                  weekday: "long",
                  month: "short",
                  day: "numeric",
               });
         }

         if (!groups.has(groupKey)) {
            groups.set(groupKey, []);
         }
         groups.get(groupKey)!.push(item);
      });

      return groups;
   }, [data, props.dateField, props.groupBy]);

   const handleItemClick = (item: TimelineItem) => {
      onAction?.("itemClick", { item }, { selectedRecord: item });
   };

   const getItemIcon = (item: TimelineItem) => {
      if (props.iconField) {
         const iconName = item[props.iconField];
         return iconMap[iconName] || Circle;
      }
      return Circle;
   };

   const getItemColor = (item: TimelineItem) => {
      if (props.colorField) {
         return item[props.colorField] || "#6366f1";
      }
      return "#6366f1";
   };

   if (loading) {
      return (
         <Card className="p-6">
            <div className="space-y-6">
               {[1, 2, 3].map((i) => (
                  <div key={i} className="animate-pulse">
                     <div className="h-4 w-32 bg-white/10 rounded mb-4" />
                     <div className="space-y-3">
                        <div className="flex gap-4">
                           <div className="w-8 h-8 rounded-full bg-white/10" />
                           <div className="flex-1">
                              <div className="h-4 w-48 bg-white/10 rounded mb-2" />
                              <div className="h-3 w-64 bg-white/5 rounded" />
                           </div>
                        </div>
                     </div>
                  </div>
               ))}
            </div>
         </Card>
      );
   }

   if (!data || data.length === 0) {
      return (
         <Card className="p-6">
            <div className="text-center py-12 text-white/40">
               <Clock className="w-12 h-12 mx-auto mb-3 opacity-50" />
               <p>No timeline items</p>
            </div>
         </Card>
      );
   }

   return (
      <Card className="p-6">
         <div className="space-y-8">
            {Array.from(groupedItems.entries()).map(([groupKey, items]) => (
               <div key={groupKey}>
                  {/* Group header */}
                  <div className="flex items-center gap-3 mb-4">
                     <div className="h-px flex-1 bg-white/10" />
                     <span className="text-sm font-medium text-white/60 px-3">
                        {groupKey}
                     </span>
                     <div className="h-px flex-1 bg-white/10" />
                  </div>

                  {/* Timeline items */}
                  <div className="relative">
                     {/* Vertical line */}
                     <div className="absolute left-4 top-0 bottom-0 w-px bg-white/10" />

                     <div className="space-y-4">
                        {items.map((item: any, index: number) => {
                           const Icon = getItemIcon(item);
                           const color = getItemColor(item);
                           const date = new Date(item[props.dateField]);

                           return (
                              <div
                                 key={item.id || index}
                                 className="relative flex gap-4 pl-2 group cursor-pointer"
                                 onClick={() => handleItemClick(item)}
                              >
                                 {/* Icon */}
                                 <div
                                    className="relative z-10 w-8 h-8 rounded-full flex items-center justify-center transition-transform group-hover:scale-110"
                                    style={{ backgroundColor: `${color}20` }}
                                 >
                                    <Icon
                                       className="w-4 h-4"
                                       style={{ color }}
                                    />
                                 </div>

                                 {/* Content */}
                                 <div className="flex-1 pb-4">
                                    <div className="bg-white/5 rounded-lg p-4 hover:bg-white/10 transition-colors">
                                       {/* Header */}
                                       <div className="flex items-start justify-between gap-4 mb-2">
                                          <h4 className="font-medium text-white">
                                             {item[props.titleField]}
                                          </h4>
                                          {props.showTime && (
                                             <span className="text-xs text-white/40 flex items-center gap-1">
                                                <Clock className="w-3 h-3" />
                                                {date.toLocaleTimeString([], {
                                                   hour: "2-digit",
                                                   minute: "2-digit",
                                                })}
                                             </span>
                                          )}
                                       </div>

                                       {/* Description */}
                                       {props.descriptionField && item[props.descriptionField] && (
                                          <p className="text-sm text-white/60 line-clamp-2">
                                             {item[props.descriptionField]}
                                          </p>
                                       )}
                                    </div>
                                 </div>
                              </div>
                           );
                        })}
                     </div>
                  </div>
               </div>
            ))}
         </div>
      </Card>
   );
}

