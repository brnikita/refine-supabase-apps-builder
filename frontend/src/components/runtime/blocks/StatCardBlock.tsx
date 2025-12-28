"use client";

import { Card } from "@/components/ui/card";
import {
   TrendingUp,
   TrendingDown,
   Users,
   DollarSign,
   ShoppingCart,
   Package,
   FileText,
   Activity,
   BarChart,
   Calendar,
   Clock,
   CheckCircle,
} from "lucide-react";
import { BlockComponentProps } from "./index";
import { StatCardProps } from "@/types/blueprint";

const iconMap: Record<string, any> = {
   users: Users,
   dollar: DollarSign,
   cart: ShoppingCart,
   package: Package,
   file: FileText,
   activity: Activity,
   chart: BarChart,
   calendar: Calendar,
   clock: Clock,
   check: CheckCircle,
};

export function StatCardBlock({
   block,
   data,
   loading,
}: BlockComponentProps) {
   const props = block.props as StatCardProps;

   // Calculate value from data if valueField is specified
   let displayValue = props.value;
   if (props.valueField && data && data.length > 0) {
      displayValue = data[0][props.valueField];
   } else if (props.query && data) {
      // Simple count query
      if (props.query.startsWith("count:")) {
         displayValue = data.length;
      }
   }

   const Icon = props.icon ? iconMap[props.icon.toLowerCase()] || Activity : Activity;
   const trendColor = props.trendDirection === "up" ? "text-green-400" : "text-red-400";
   const TrendIcon = props.trendDirection === "up" ? TrendingUp : TrendingDown;

   const cardColor = props.color || "#6366f1";

   if (loading) {
      return (
         <Card className="p-6">
            <div className="animate-pulse">
               <div className="h-4 w-24 bg-white/10 rounded mb-3" />
               <div className="h-8 w-16 bg-white/10 rounded" />
            </div>
         </Card>
      );
   }

   return (
      <Card
         className="p-6 relative overflow-hidden"
         style={{
            background: `linear-gradient(135deg, ${cardColor}15 0%, transparent 60%)`,
         }}
      >
         {/* Background Icon */}
         <div
            className="absolute -right-4 -bottom-4 opacity-10"
            style={{ color: cardColor }}
         >
            <Icon className="w-24 h-24" />
         </div>

         {/* Content */}
         <div className="relative">
            <div className="flex items-center justify-between mb-2">
               <p className="text-sm font-medium text-white/60">{props.title}</p>
               <div
                  className="w-10 h-10 rounded-lg flex items-center justify-center"
                  style={{ backgroundColor: `${cardColor}20` }}
               >
                  <Icon className="w-5 h-5" style={{ color: cardColor }} />
               </div>
            </div>

            <div className="flex items-end gap-3">
               <p className="text-3xl font-bold text-white">
                  {typeof displayValue === "number"
                     ? displayValue.toLocaleString()
                     : displayValue ?? "—"}
               </p>

               {props.trend !== undefined && (
                  <div className={`flex items-center gap-1 text-sm ${trendColor} mb-1`}>
                     <TrendIcon className="w-4 h-4" />
                     <span>{Math.abs(props.trend)}%</span>
                  </div>
               )}
            </div>
         </div>
      </Card>
   );
}

