"use client";

import { useState, useMemo } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
   Search,
   ChevronUp,
   ChevronDown,
   Eye,
   Edit,
   Trash2,
   Plus,
   ChevronLeft,
   ChevronRight,
} from "lucide-react";
import { BlockComponentProps } from "./index";
import { TableProps, TableColumnDef } from "@/types/blueprint";

export function TableBlock({
   block,
   data,
   loading,
   onAction,
   onDelete,
}: BlockComponentProps) {
   const props = block.props as TableProps;
   const [searchTerm, setSearchTerm] = useState("");
   const [sortField, setSortField] = useState<string | null>(null);
   const [sortDirection, setSortDirection] = useState<"asc" | "desc">("asc");
   const [currentPage, setCurrentPage] = useState(1);

   const pageSize = props.pagination?.pageSize || 10;

   // Filter data by search term
   const filteredData = useMemo(() => {
      if (!searchTerm || !props.allowSearch) return data;
      const term = searchTerm.toLowerCase();
      return data.filter((row) =>
         props.columns.some((col) => {
            const value = row[col.field];
            return value && String(value).toLowerCase().includes(term);
         })
      );
   }, [data, searchTerm, props.allowSearch, props.columns]);

   // Sort data
   const sortedData = useMemo(() => {
      if (!sortField) return filteredData;
      return [...filteredData].sort((a, b) => {
         const aVal = a[sortField];
         const bVal = b[sortField];
         if (aVal === bVal) return 0;
         if (aVal === null || aVal === undefined) return 1;
         if (bVal === null || bVal === undefined) return -1;
         const comparison = aVal < bVal ? -1 : 1;
         return sortDirection === "asc" ? comparison : -comparison;
      });
   }, [filteredData, sortField, sortDirection]);

   // Paginate data
   const paginatedData = useMemo(() => {
      const start = (currentPage - 1) * pageSize;
      return sortedData.slice(start, start + pageSize);
   }, [sortedData, currentPage, pageSize]);

   const totalPages = Math.ceil(sortedData.length / pageSize);

   const handleSort = (field: string) => {
      if (!props.allowSort) return;
      if (sortField === field) {
         setSortDirection((d) => (d === "asc" ? "desc" : "asc"));
      } else {
         setSortField(field);
         setSortDirection("asc");
      }
   };

   const renderCellValue = (row: any, column: TableColumnDef) => {
      const value = row[column.field];

      if (value === null || value === undefined) {
         return <span className="text-white/40">—</span>;
      }

      switch (column.type) {
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
                  alt=""
                  className="w-10 h-10 rounded object-cover"
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
            return String(value).substring(0, 50);
      }
   };

   const handleRowAction = (action: string, row: any) => {
      if (action === "delete" && onDelete) {
         onDelete(row.id);
      } else if (onAction) {
         onAction(action, { record: row }, { selectedRecord: row });
      }
   };

   if (loading) {
      return (
         <Card className="p-8">
            <div className="flex items-center justify-center">
               <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500" />
            </div>
         </Card>
      );
   }

   return (
      <Card className="overflow-hidden">
         {/* Toolbar */}
         {(props.allowSearch || props.rowActions?.includes("create" as any)) && (
            <div className="p-4 border-b border-white/10 flex items-center justify-between gap-4">
               {props.allowSearch && (
                  <div className="relative flex-1 max-w-sm">
                     <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/40" />
                     <Input
                        placeholder="Search..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="pl-10"
                     />
                  </div>
               )}
               <Button
                  onClick={() => onAction?.("create", {}, {})}
                  size="sm"
               >
                  <Plus className="w-4 h-4 mr-2" />
                  Add New
               </Button>
            </div>
         )}

         {/* Table */}
         <div className="overflow-x-auto">
            <table className="w-full">
               <thead>
                  <tr className="border-b border-white/10">
                     {props.columns.map((column) => (
                        <th
                           key={column.field}
                           className={`px-4 py-3 text-left text-sm font-medium text-white/60 uppercase tracking-wider ${
                              column.sortable !== false && props.allowSort
                                 ? "cursor-pointer hover:text-white"
                                 : ""
                           }`}
                           style={{ width: column.width }}
                           onClick={() =>
                              column.sortable !== false && handleSort(column.field)
                           }
                        >
                           <div className="flex items-center gap-2">
                              {column.label}
                              {sortField === column.field && (
                                 sortDirection === "asc" ? (
                                    <ChevronUp className="w-4 h-4" />
                                 ) : (
                                    <ChevronDown className="w-4 h-4" />
                                 )
                              )}
                           </div>
                        </th>
                     ))}
                     {props.rowActions && props.rowActions.length > 0 && (
                        <th className="px-4 py-3 text-right text-sm font-medium text-white/60 uppercase tracking-wider">
                           Actions
                        </th>
                     )}
                  </tr>
               </thead>
               <tbody className="divide-y divide-white/5">
                  {paginatedData.length === 0 ? (
                     <tr>
                        <td
                           colSpan={props.columns.length + (props.rowActions ? 1 : 0)}
                           className="px-4 py-12 text-center text-white/40"
                        >
                           {props.emptyMessage || "No data available"}
                        </td>
                     </tr>
                  ) : (
                     paginatedData.map((row, index) => (
                        <tr
                           key={row.id || index}
                           className="hover:bg-white/5 transition-colors"
                        >
                           {props.columns.map((column) => (
                              <td key={column.field} className="px-4 py-3 text-white/80">
                                 {renderCellValue(row, column)}
                              </td>
                           ))}
                           {props.rowActions && props.rowActions.length > 0 && (
                              <td className="px-4 py-3 text-right">
                                 <div className="flex items-center justify-end gap-1">
                                    {props.rowActions.includes("view") && (
                                       <Button
                                          variant="ghost"
                                          size="sm"
                                          onClick={() => handleRowAction("view", row)}
                                       >
                                          <Eye className="w-4 h-4" />
                                       </Button>
                                    )}
                                    {props.rowActions.includes("edit") && (
                                       <Button
                                          variant="ghost"
                                          size="sm"
                                          onClick={() => handleRowAction("edit", row)}
                                       >
                                          <Edit className="w-4 h-4" />
                                       </Button>
                                    )}
                                    {props.rowActions.includes("delete") && (
                                       <Button
                                          variant="ghost"
                                          size="sm"
                                          className="text-red-400 hover:text-red-300"
                                          onClick={() => handleRowAction("delete", row)}
                                       >
                                          <Trash2 className="w-4 h-4" />
                                       </Button>
                                    )}
                                 </div>
                              </td>
                           )}
                        </tr>
                     ))
                  )}
               </tbody>
            </table>
         </div>

         {/* Pagination */}
         {totalPages > 1 && (
            <div className="p-4 border-t border-white/10 flex items-center justify-between">
               <p className="text-sm text-white/60">
                  Showing {(currentPage - 1) * pageSize + 1} to{" "}
                  {Math.min(currentPage * pageSize, sortedData.length)} of{" "}
                  {sortedData.length} results
               </p>
               <div className="flex items-center gap-2">
                  <Button
                     variant="secondary"
                     size="sm"
                     disabled={currentPage === 1}
                     onClick={() => setCurrentPage((p) => p - 1)}
                  >
                     <ChevronLeft className="w-4 h-4" />
                  </Button>
                  <span className="text-sm text-white/80 px-2">
                     Page {currentPage} of {totalPages}
                  </span>
                  <Button
                     variant="secondary"
                     size="sm"
                     disabled={currentPage === totalPages}
                     onClick={() => setCurrentPage((p) => p + 1)}
                  >
                     <ChevronRight className="w-4 h-4" />
                  </Button>
               </div>
            </div>
         )}
      </Card>
   );
}

