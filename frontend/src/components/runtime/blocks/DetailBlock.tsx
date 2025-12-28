"use client";

import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { BlockComponentProps } from "./index";
import { DetailProps, DetailFieldDef } from "@/types/blueprint";

export function DetailBlock({
   block,
   data,
   loading,
   context,
}: BlockComponentProps) {
   const props = block.props as DetailProps;
   const record = context?.selectedRecord || (data && data[0]);

   if (loading) {
      return (
         <Card className="p-6">
            <div className="animate-pulse space-y-4">
               {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="space-y-2">
                     <div className="h-4 w-24 bg-white/10 rounded" />
                     <div className="h-6 w-48 bg-white/10 rounded" />
                  </div>
               ))}
            </div>
         </Card>
      );
   }

   if (!record) {
      return (
         <Card className="p-6">
            <p className="text-white/60 text-center">No record selected</p>
         </Card>
      );
   }

   const renderFieldValue = (field: DetailFieldDef) => {
      const value = record[field.name];

      if (value === null || value === undefined) {
         return <span className="text-white/40">—</span>;
      }

      switch (field.type) {
         case "badge":
            return (
               <Badge
                  variant={
                     value === "done" || value === "completed" || value === "active"
                        ? "success"
                        : value === "pending" || value === "in_progress"
                        ? "warning"
                        : "default"
                  }
               >
                  {String(value).replace(/_/g, " ")}
               </Badge>
            );
         case "boolean":
            return (
               <Badge variant={value ? "success" : "default"}>
                  {value ? "Yes" : "No"}
               </Badge>
            );
         case "date":
            return new Date(value).toLocaleDateString();
         case "datetime":
            return new Date(value).toLocaleString();
         case "image":
            return (
               <img
                  src={value}
                  alt={field.label}
                  className="max-w-xs rounded-lg"
               />
            );
         case "link":
            return (
               <a
                  href={value}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary-400 hover:underline"
               >
                  {value}
               </a>
            );
         default:
            return <span className="text-white">{String(value)}</span>;
      }
   };

   const layoutClass = {
      vertical: "space-y-4",
      horizontal: "grid grid-cols-2 gap-4",
      grid: "grid grid-cols-3 gap-4",
   }[props.layout || "vertical"];

   return (
      <Card className="p-6">
         <dl className={layoutClass}>
            {props.fields?.map((field) => (
               <div
                  key={field.name}
                  className={`${
                     props.layout !== "vertical" ? "" : "border-b border-white/10 pb-3"
                  }`}
               >
                  <dt className="text-sm text-white/60 mb-1">{field.label}</dt>
                  <dd>{renderFieldValue(field)}</dd>
               </div>
            ))}
         </dl>
      </Card>
   );
}

