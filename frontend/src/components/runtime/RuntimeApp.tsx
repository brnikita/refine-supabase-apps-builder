"use client";

import { useState, useMemo } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
   Menu,
   X,
   Home,
   List,
   Plus,
   Edit,
   Eye,
   Trash2,
   ChevronRight,
   Database,
   Users,
   FileText,
   Package,
   Settings,
   BarChart,
} from "lucide-react";

interface RuntimeAppProps {
   app: { id: string; name: string; slug: string };
   blueprint: any;
   runtimeConfig: { db_schema: string; base_path: string };
}

// Icon mapping for navigation
const iconMap: Record<string, any> = {
   home: Home,
   list: List,
   users: Users,
   file: FileText,
   package: Package,
   settings: Settings,
   chart: BarChart,
   database: Database,
};

export function RuntimeApp({ app, blueprint, runtimeConfig }: RuntimeAppProps) {
   const [sidebarOpen, setSidebarOpen] = useState(true);
   const [activeResource, setActiveResource] = useState<string | null>(
      blueprint.ui?.resources?.[0]?.name || null
   );
   const [activeView, setActiveView] = useState<"list" | "create" | "edit" | "show">("list");
   const [selectedRecord, setSelectedRecord] = useState<any>(null);

   // Generate mock data for demonstration
   const mockData = useMemo(() => {
      const data: Record<string, any[]> = {};

      blueprint.data?.tables?.forEach((table: any) => {
         const records = [];
         for (let i = 1; i <= 5; i++) {
            const record: any = { id: `${i}` };
            table.columns?.forEach((col: any) => {
               if (col.type === "text") {
                  record[col.name] = `Sample ${col.name} ${i}`;
               } else if (col.type === "int") {
                  record[col.name] = i * 10;
               } else if (col.type === "bool") {
                  record[col.name] = i % 2 === 0;
               } else if (col.type === "date" || col.type === "timestamptz") {
                  record[col.name] = new Date().toISOString();
               }
            });
            record.created_at = new Date().toISOString();
            records.push(record);
         }
         data[table.name] = records;
      });

      return data;
   }, [blueprint]);

   const currentResource = blueprint.ui?.resources?.find(
      (r: any) => r.name === activeResource
   );

   const currentTable = blueprint.data?.tables?.find(
      (t: any) => t.name === currentResource?.table
   );

   const renderNavItem = (item: any) => {
      const Icon = iconMap[item.icon?.toLowerCase()] || List;
      const isActive = activeResource === item.name;

      return (
         <button
            key={item.name}
            onClick={() => {
               setActiveResource(item.name);
               setActiveView("list");
               setSelectedRecord(null);
            }}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all ${
               isActive
                  ? "bg-primary-500/20 text-primary-400 border border-primary-500/30"
                  : "text-white/70 hover:text-white hover:bg-white/10"
            }`}
         >
            <Icon className="w-5 h-5" />
            <span className="font-medium">{item.label}</span>
         </button>
      );
   };

   const renderListView = () => {
      if (!currentResource || !currentTable) return null;

      const records = mockData[currentTable.name] || [];
      const columns = currentResource.list?.columns || currentTable.columns?.map((c: any) => c.name) || [];

      return (
         <div>
            <div className="flex items-center justify-between mb-6">
               <h2 className="text-2xl font-bold text-white">{currentResource.label}</h2>
               {currentResource.views?.create !== false && (
                  <Button onClick={() => setActiveView("create")}>
                     <Plus className="w-4 h-4 mr-2" />
                     Create New
                  </Button>
               )}
            </div>

            <Card className="overflow-hidden">
               <div className="overflow-x-auto">
                  <table className="w-full">
                     <thead>
                        <tr className="border-b border-white/10">
                           {columns.slice(0, 5).map((col: string) => (
                              <th
                                 key={col}
                                 className="px-4 py-3 text-left text-sm font-medium text-white/60 uppercase tracking-wider"
                              >
                                 {col.replace(/_/g, " ")}
                              </th>
                           ))}
                           <th className="px-4 py-3 text-right text-sm font-medium text-white/60 uppercase tracking-wider">
                              Actions
                           </th>
                        </tr>
                     </thead>
                     <tbody className="divide-y divide-white/5">
                        {records.map((record: any) => (
                           <tr key={record.id} className="hover:bg-white/5 transition-colors">
                              {columns.slice(0, 5).map((col: string) => (
                                 <td key={col} className="px-4 py-3 text-white/80">
                                    {typeof record[col] === "boolean" ? (
                                       <Badge variant={record[col] ? "success" : "default"}>
                                          {record[col] ? "Yes" : "No"}
                                       </Badge>
                                    ) : (
                                       String(record[col] || "-").substring(0, 30)
                                    )}
                                 </td>
                              ))}
                              <td className="px-4 py-3 text-right">
                                 <div className="flex items-center justify-end gap-2">
                                    {currentResource.views?.show !== false && (
                                       <Button
                                          variant="ghost"
                                          size="sm"
                                          onClick={() => {
                                             setSelectedRecord(record);
                                             setActiveView("show");
                                          }}
                                       >
                                          <Eye className="w-4 h-4" />
                                       </Button>
                                    )}
                                    {currentResource.views?.edit !== false && (
                                       <Button
                                          variant="ghost"
                                          size="sm"
                                          onClick={() => {
                                             setSelectedRecord(record);
                                             setActiveView("edit");
                                          }}
                                       >
                                          <Edit className="w-4 h-4" />
                                       </Button>
                                    )}
                                    <Button
                                       variant="ghost"
                                       size="sm"
                                       className="text-red-400 hover:text-red-300"
                                    >
                                       <Trash2 className="w-4 h-4" />
                                    </Button>
                                 </div>
                              </td>
                           </tr>
                        ))}
                     </tbody>
                  </table>
               </div>
            </Card>
         </div>
      );
   };

   const renderFormView = (isEdit: boolean) => {
      if (!currentResource || !currentTable) return null;

      const fields = isEdit
         ? currentResource.forms?.editFields || currentTable.columns
         : currentResource.forms?.createFields || currentTable.columns;

      return (
         <div>
            <div className="flex items-center gap-2 mb-6">
               <button
                  onClick={() => {
                     setActiveView("list");
                     setSelectedRecord(null);
                  }}
                  className="text-white/60 hover:text-white"
               >
                  {currentResource.label}
               </button>
               <ChevronRight className="w-4 h-4 text-white/40" />
               <span className="text-white">{isEdit ? "Edit" : "Create"}</span>
            </div>

            <Card className="max-w-2xl">
               <h2 className="text-xl font-bold text-white mb-6">
                  {isEdit ? `Edit ${currentResource.label}` : `Create ${currentResource.label}`}
               </h2>

               <form className="space-y-4">
                  {fields?.map((field: any) => {
                     const fieldName = field.name || field;
                     const fieldLabel = field.label || fieldName.replace(/_/g, " ");
                     const fieldType = field.widget || "text";

                     return (
                        <div key={fieldName}>
                           <label className="block text-sm font-medium text-white/80 mb-1.5 capitalize">
                              {fieldLabel}
                           </label>
                           {fieldType === "select" ? (
                              <select className="w-full px-4 py-2.5 rounded-lg bg-white/5 border border-white/10 text-white">
                                 <option value="">Select...</option>
                                 {field.options?.map((opt: any) => (
                                    <option key={opt} value={opt}>
                                       {opt}
                                    </option>
                                 ))}
                              </select>
                           ) : fieldType === "checkbox" ? (
                              <input
                                 type="checkbox"
                                 className="w-5 h-5 rounded bg-white/5 border border-white/10"
                                 defaultChecked={isEdit ? selectedRecord?.[fieldName] : false}
                              />
                           ) : (
                              <input
                                 type={fieldType === "number" ? "number" : "text"}
                                 className="w-full px-4 py-2.5 rounded-lg bg-white/5 border border-white/10 text-white placeholder-white/40"
                                 placeholder={`Enter ${fieldLabel.toLowerCase()}`}
                                 defaultValue={isEdit ? selectedRecord?.[fieldName] : ""}
                              />
                           )}
                        </div>
                     );
                  })}

                  <div className="flex gap-3 pt-4">
                     <Button type="button">
                        {isEdit ? "Save Changes" : "Create"}
                     </Button>
                     <Button
                        type="button"
                        variant="secondary"
                        onClick={() => {
                           setActiveView("list");
                           setSelectedRecord(null);
                        }}
                     >
                        Cancel
                     </Button>
                  </div>
               </form>
            </Card>
         </div>
      );
   };

   const renderShowView = () => {
      if (!currentResource || !selectedRecord) return null;

      return (
         <div>
            <div className="flex items-center gap-2 mb-6">
               <button
                  onClick={() => {
                     setActiveView("list");
                     setSelectedRecord(null);
                  }}
                  className="text-white/60 hover:text-white"
               >
                  {currentResource.label}
               </button>
               <ChevronRight className="w-4 h-4 text-white/40" />
               <span className="text-white">View</span>
            </div>

            <Card className="max-w-2xl">
               <div className="flex items-center justify-between mb-6">
                  <h2 className="text-xl font-bold text-white">
                     {currentResource.label} Details
                  </h2>
                  <div className="flex gap-2">
                     <Button
                        variant="secondary"
                        size="sm"
                        onClick={() => setActiveView("edit")}
                     >
                        <Edit className="w-4 h-4 mr-1" />
                        Edit
                     </Button>
                  </div>
               </div>

               <dl className="space-y-4">
                  {Object.entries(selectedRecord).map(([key, value]) => (
                     <div key={key} className="border-b border-white/10 pb-3">
                        <dt className="text-sm text-white/60 capitalize mb-1">
                           {key.replace(/_/g, " ")}
                        </dt>
                        <dd className="text-white">
                           {typeof value === "boolean" ? (
                              <Badge variant={value ? "success" : "default"}>
                                 {value ? "Yes" : "No"}
                              </Badge>
                           ) : (
                              String(value || "-")
                           )}
                        </dd>
                     </div>
                  ))}
               </dl>
            </Card>
         </div>
      );
   };

   return (
      <div className="min-h-screen bg-[#0a0a0f]">
         {/* Sidebar */}
         <aside
            className={`fixed top-0 left-0 h-full w-64 bg-black/40 border-r border-white/10 transition-transform z-40 ${
               sidebarOpen ? "translate-x-0" : "-translate-x-full"
            }`}
         >
            {/* App Header */}
            <div className="p-4 border-b border-white/10">
               <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl gradient-button flex items-center justify-center">
                     <Database className="w-5 h-5 text-white" />
                  </div>
                  <div>
                     <h1 className="font-semibold text-white">{app.name}</h1>
                     <p className="text-xs text-white/50">/{app.slug}</p>
                  </div>
               </div>
            </div>

            {/* Navigation */}
            <nav className="p-4 space-y-1">
               {blueprint.ui?.navigation?.map(renderNavItem)}
               {!blueprint.ui?.navigation?.length &&
                  blueprint.ui?.resources?.map((resource: any) =>
                     renderNavItem({
                        name: resource.name,
                        label: resource.label,
                        icon: "list",
                     })
                  )}
            </nav>
         </aside>

         {/* Main Content */}
         <main
            className={`transition-all ${sidebarOpen ? "ml-64" : "ml-0"}`}
         >
            {/* Top Bar */}
            <header className="sticky top-0 z-30 bg-[#0a0a0f]/80 backdrop-blur-sm border-b border-white/10">
               <div className="flex items-center gap-4 px-6 py-4">
                  <button
                     onClick={() => setSidebarOpen(!sidebarOpen)}
                     className="p-2 rounded-lg text-white/60 hover:text-white hover:bg-white/10 transition-colors"
                  >
                     {sidebarOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
                  </button>

                  <div className="flex items-center gap-2 text-white/60">
                     <Home className="w-4 h-4" />
                     <ChevronRight className="w-4 h-4" />
                     <span className="text-white">{currentResource?.label || "Home"}</span>
                  </div>
               </div>
            </header>

            {/* Page Content */}
            <div className="p-6">
               {activeView === "list" && renderListView()}
               {activeView === "create" && renderFormView(false)}
               {activeView === "edit" && renderFormView(true)}
               {activeView === "show" && renderShowView()}
            </div>
         </main>
      </div>
   );
}

