"use client";

import { useMemo } from "react";
import { Card } from "@/components/ui/card";
import { BlockComponentProps } from "./index";
import { ChartProps } from "@/types/blueprint";

// Simple chart implementation without external dependencies
// In production, you'd use recharts, chart.js, or similar

export function ChartBlock({
   block,
   data,
   loading,
}: BlockComponentProps) {
   const props = block.props as ChartProps;

   const chartData = useMemo(() => {
      if (!data || data.length === 0) return [];

      // Group and aggregate data
      if (props.groupField) {
         const groups: Record<string, number> = {};
         data.forEach((item) => {
            const key = item[props.groupField!] || "Unknown";
            if (props.aggregation === "count") {
               groups[key] = (groups[key] || 0) + 1;
            } else if (props.yField) {
               const value = parseFloat(item[props.yField]) || 0;
               switch (props.aggregation) {
                  case "sum":
                     groups[key] = (groups[key] || 0) + value;
                     break;
                  case "avg":
                     // Simplified avg - would need count tracking in real impl
                     groups[key] = (groups[key] || 0) + value;
                     break;
                  case "max":
                     groups[key] = Math.max(groups[key] || -Infinity, value);
                     break;
                  case "min":
                     groups[key] = Math.min(groups[key] || Infinity, value);
                     break;
                  default:
                     groups[key] = (groups[key] || 0) + value;
               }
            }
         });
         return Object.entries(groups).map(([label, value]) => ({ label, value }));
      }

      // Simple x/y mapping
      return data.map((item) => ({
         label: item[props.xField || "label"] || "",
         value: parseFloat(item[props.yField || "value"]) || 0,
      }));
   }, [data, props]);

   const maxValue = Math.max(...chartData.map((d) => d.value), 1);

   const defaultColors = [
      "#6366f1", "#8b5cf6", "#a855f7", "#d946ef",
      "#ec4899", "#f43f5e", "#f97316", "#eab308",
      "#22c55e", "#14b8a6", "#06b6d4", "#3b82f6",
   ];
   const colors = props.colors || defaultColors;

   if (loading) {
      return (
         <Card className="p-6">
            <div className="animate-pulse">
               <div className="h-48 bg-white/10 rounded" />
            </div>
         </Card>
      );
   }

   if (chartData.length === 0) {
      return (
         <Card className="p-6">
            <div className="h-48 flex items-center justify-center text-white/40">
               No data available for chart
            </div>
         </Card>
      );
   }

   // Render different chart types
   const renderBarChart = () => (
      <div className="flex items-end gap-2 h-48">
         {chartData.map((item, index) => (
            <div key={index} className="flex-1 flex flex-col items-center gap-2">
               <div
                  className="w-full rounded-t transition-all duration-300 hover:opacity-80"
                  style={{
                     height: `${(item.value / maxValue) * 100}%`,
                     backgroundColor: colors[index % colors.length],
                     minHeight: "4px",
                  }}
                  title={`${item.label}: ${item.value}`}
               />
               <span className="text-xs text-white/60 truncate max-w-full">
                  {item.label}
               </span>
            </div>
         ))}
      </div>
   );

   const renderPieChart = () => {
      const total = chartData.reduce((sum, d) => sum + d.value, 0);
      let currentAngle = 0;

      return (
         <div className="flex items-center gap-8">
            <div className="relative w-48 h-48">
               <svg viewBox="0 0 100 100" className="w-full h-full -rotate-90">
                  {chartData.map((item, index) => {
                     const percentage = (item.value / total) * 100;
                     const angle = (percentage / 100) * 360;
                     const startAngle = currentAngle;
                     currentAngle += angle;

                     // Calculate arc path
                     const startRad = (startAngle * Math.PI) / 180;
                     const endRad = ((startAngle + angle) * Math.PI) / 180;
                     const x1 = 50 + 40 * Math.cos(startRad);
                     const y1 = 50 + 40 * Math.sin(startRad);
                     const x2 = 50 + 40 * Math.cos(endRad);
                     const y2 = 50 + 40 * Math.sin(endRad);
                     const largeArc = angle > 180 ? 1 : 0;

                     return (
                        <path
                           key={index}
                           d={`M 50 50 L ${x1} ${y1} A 40 40 0 ${largeArc} 1 ${x2} ${y2} Z`}
                           fill={colors[index % colors.length]}
                           className="hover:opacity-80 transition-opacity cursor-pointer"
                        />
                     );
                  })}
                  {/* Center hole for donut */}
                  {props.chartType === "donut" && (
                     <circle cx="50" cy="50" r="25" fill="#0a0a0f" />
                  )}
               </svg>
            </div>

            {/* Legend */}
            {props.showLegend !== false && (
               <div className="space-y-2">
                  {chartData.map((item, index) => (
                     <div key={index} className="flex items-center gap-2">
                        <div
                           className="w-3 h-3 rounded-full"
                           style={{ backgroundColor: colors[index % colors.length] }}
                        />
                        <span className="text-sm text-white/80">{item.label}</span>
                        <span className="text-sm text-white/40">
                           ({((item.value / total) * 100).toFixed(1)}%)
                        </span>
                     </div>
                  ))}
               </div>
            )}
         </div>
      );
   };

   const renderLineChart = () => (
      <div className="relative h-48">
         {/* Grid lines */}
         {props.showGrid !== false && (
            <div className="absolute inset-0 flex flex-col justify-between">
               {[0, 1, 2, 3, 4].map((i) => (
                  <div key={i} className="border-t border-white/10 w-full" />
               ))}
            </div>
         )}

         {/* Line */}
         <svg className="absolute inset-0 w-full h-full">
            <polyline
               fill="none"
               stroke={colors[0]}
               strokeWidth="2"
               points={chartData
                  .map((item, index) => {
                     const x = (index / (chartData.length - 1)) * 100;
                     const y = 100 - (item.value / maxValue) * 100;
                     return `${x}%,${y}%`;
                  })
                  .join(" ")}
            />
            {/* Dots */}
            {chartData.map((item, index) => {
               const x = (index / (chartData.length - 1)) * 100;
               const y = 100 - (item.value / maxValue) * 100;
               return (
                  <circle
                     key={index}
                     cx={`${x}%`}
                     cy={`${y}%`}
                     r="4"
                     fill={colors[0]}
                     className="hover:r-6 transition-all cursor-pointer"
                  />
               );
            })}
         </svg>

         {/* X-axis labels */}
         <div className="absolute bottom-0 left-0 right-0 flex justify-between transform translate-y-6">
            {chartData.map((item, index) => (
               <span key={index} className="text-xs text-white/60">
                  {item.label}
               </span>
            ))}
         </div>
      </div>
   );

   const renderAreaChart = () => (
      <div className="relative h-48">
         <svg className="absolute inset-0 w-full h-full">
            <defs>
               <linearGradient id={`gradient-${block.id}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor={colors[0]} stopOpacity="0.3" />
                  <stop offset="100%" stopColor={colors[0]} stopOpacity="0" />
               </linearGradient>
            </defs>
            {/* Area */}
            <polygon
               fill={`url(#gradient-${block.id})`}
               points={`0,100 ${chartData
                  .map((item, index) => {
                     const x = (index / (chartData.length - 1)) * 100;
                     const y = 100 - (item.value / maxValue) * 100;
                     return `${x},${y}`;
                  })
                  .join(" ")} 100,100`}
            />
            {/* Line */}
            <polyline
               fill="none"
               stroke={colors[0]}
               strokeWidth="2"
               points={chartData
                  .map((item, index) => {
                     const x = (index / (chartData.length - 1)) * 100;
                     const y = 100 - (item.value / maxValue) * 100;
                     return `${x},${y}`;
                  })
                  .join(" ")}
            />
         </svg>
      </div>
   );

   return (
      <Card className="p-6">
         {props.chartType === "pie" || props.chartType === "donut"
            ? renderPieChart()
            : props.chartType === "line"
            ? renderLineChart()
            : props.chartType === "area"
            ? renderAreaChart()
            : renderBarChart()}
      </Card>
   );
}

