"use client";

import { useState, useMemo, useCallback } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Modal } from "@/components/ui/modal";
import {
   Menu,
   X,
   Home,
   List,
   ChevronRight,
   Database,
   Users,
   FileText,
   Package,
   Settings,
   BarChart,
   Calendar,
   MessageSquare,
   LayoutDashboard,
   Kanban,
   Image,
   Clock,
   FolderTree,
} from "lucide-react";
import { BlueprintV2, PageSpec, ModalSpec, NavItem, isBlueprintV2 } from "@/types/blueprint";
import { LayoutRenderer } from "./LayoutRenderer";

interface RuntimeAppV2Props {
   app: { id: string; name: string; slug: string };
   blueprint: BlueprintV2 | any;
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
   calendar: Calendar,
   message: MessageSquare,
   dashboard: LayoutDashboard,
   kanban: Kanban,
   "layout-kanban": Kanban,
   image: Image,
   clock: Clock,
   tree: FolderTree,
};

export function RuntimeAppV2({ app, blueprint, runtimeConfig }: RuntimeAppV2Props) {
   const [sidebarOpen, setSidebarOpen] = useState(true);
   const [activePage, setActivePage] = useState<string>(
      blueprint.ui?.pages?.[0]?.id || ""
   );
   const [activeModal, setActiveModal] = useState<string | null>(null);
   const [pageVariables, setPageVariables] = useState<Record<string, any>>({});
   const [selectedRecord, setSelectedRecord] = useState<any>(null);

   // Check if this is a V2 blueprint
   const isV2 = isBlueprintV2(blueprint);

   // Generate mock data for all tables
   const mockData = useMemo(() => {
      const data: Record<string, any[]> = {};

      blueprint.data?.tables?.forEach((table: any) => {
         const records = [];
         const recordCount = Math.floor(Math.random() * 10) + 5;

         for (let i = 1; i <= recordCount; i++) {
            const record: any = { id: `${i}` };

            table.columns?.forEach((col: any) => {
               switch (col.type) {
                  case "text":
                     if (col.name.includes("title") || col.name.includes("name")) {
                        record[col.name] = `${col.name.replace(/_/g, " ")} ${i}`;
                     } else if (col.name.includes("description")) {
                        record[col.name] = `This is a sample description for item ${i}. It contains some text to demonstrate the layout.`;
                     } else if (col.name.includes("status")) {
                        const statuses = ["backlog", "todo", "in_progress", "review", "done"];
                        record[col.name] = statuses[i % statuses.length];
                     } else if (col.name.includes("priority")) {
                        const priorities = ["low", "medium", "high"];
                        record[col.name] = priorities[i % priorities.length];
                     } else if (col.name.includes("email")) {
                        record[col.name] = `user${i}@example.com`;
                     } else if (col.name.includes("content") || col.name.includes("message")) {
                        record[col.name] = `This is message content ${i}. Lorem ipsum dolor sit amet.`;
                     } else if (col.name.includes("category")) {
                        const categories = ["meeting", "deadline", "reminder", "personal"];
                        record[col.name] = categories[i % categories.length];
                     } else if (col.name.includes("avatar") || col.name.includes("image")) {
                        record[col.name] = `https://api.dicebear.com/7.x/avataaars/svg?seed=${i}`;
                     } else {
                        record[col.name] = `${col.name.replace(/_/g, " ")} ${i}`;
                     }
                     break;
                  case "int":
                     record[col.name] = i * 10 + Math.floor(Math.random() * 100);
                     break;
                  case "float":
                     record[col.name] = (i * 10.5 + Math.random() * 50).toFixed(2);
                     break;
                  case "bool":
                     record[col.name] = i % 2 === 0;
                     break;
                  case "date":
                     const date = new Date();
                     date.setDate(date.getDate() + i - 5);
                     record[col.name] = date.toISOString().split("T")[0];
                     break;
                  case "timestamptz":
                     const ts = new Date();
                     ts.setDate(ts.getDate() + i - 5);
                     ts.setHours(9 + (i % 8), (i * 15) % 60);
                     record[col.name] = ts.toISOString();
                     break;
                  case "uuid":
                     record[col.name] = `uuid-${i}-${Math.random().toString(36).slice(2, 10)}`;
                     break;
                  case "jsonb":
                     record[col.name] = { key: `value${i}` };
                     break;
               }
            });

            record.created_at = new Date(Date.now() - i * 86400000).toISOString();
            record.updated_at = new Date().toISOString();
            records.push(record);
         }

         data[table.name] = records;
      });

      return data;
   }, [blueprint]);

   // Get current page
   const currentPage = useMemo(() => {
      if (!isV2) return null;
      return blueprint.ui?.pages?.find((p: PageSpec) => p.id === activePage) || null;
   }, [blueprint, activePage, isV2]);

   // Get current modal
   const currentModal = useMemo(() => {
      if (!activeModal || !isV2) return null;
      return blueprint.ui?.modals?.find((m: ModalSpec) => m.id === activeModal) || null;
   }, [blueprint, activeModal, isV2]);

   // Navigation items from pages
   const navItems = useMemo(() => {
      if (!isV2) return [];
      if (blueprint.ui?.navigation?.length > 0) {
         return blueprint.ui.navigation;
      }
      // Generate from pages
      return blueprint.ui?.pages?.map((page: PageSpec) => ({
         name: page.id,
         label: page.title,
         icon: page.icon || "list",
         route: page.route,
      })) || [];
   }, [blueprint, isV2]);

   // Context for blocks
   const context = useMemo(() => ({
      pageVariables,
      selectedRecord,
      user: { id: "1", name: "Demo User", email: "demo@example.com" },
   }), [pageVariables, selectedRecord]);

   // Handle actions from blocks
   const handleAction = useCallback((action: string, config: any, actionContext?: any) => {
      console.log("Action:", action, config, actionContext);

      switch (action) {
         case "navigate":
            const targetPage = blueprint.ui?.pages?.find(
               (p: PageSpec) => p.route === config.route || p.id === config.route
            );
            if (targetPage) {
               setActivePage(targetPage.id);
            }
            break;

         case "openModal":
            setActiveModal(config.modal);
            if (actionContext?.selectedRecord) {
               setSelectedRecord(actionContext.selectedRecord);
            }
            break;

         case "closeModal":
            setActiveModal(null);
            break;

         case "setVariable":
            setPageVariables((prev) => ({
               ...prev,
               [config.name]: config.value,
            }));
            break;

         case "view":
         case "edit":
         case "cardClick":
            if (actionContext?.selectedRecord) {
               setSelectedRecord(actionContext.selectedRecord);
               // Try to open a detail modal if one exists
               const detailModal = blueprint.ui?.modals?.find(
                  (m: ModalSpec) => m.id.includes("detail") || m.id.includes("edit")
               );
               if (detailModal) {
                  setActiveModal(detailModal.id);
               }
            }
            break;

         case "create":
         case "createClick":
            // Try to open a create modal if one exists
            const createModal = blueprint.ui?.modals?.find(
               (m: ModalSpec) => m.id.includes("create") || m.id.includes("new")
            );
            if (createModal) {
               setSelectedRecord(null);
               setActiveModal(createModal.id);
            }
            break;

         case "submit":
            // Close modal after form submission
            setActiveModal(null);
            break;

         case "cancel":
            setActiveModal(null);
            break;

         default:
            console.log("Unhandled action:", action);
      }
   }, [blueprint]);

   // CRUD operations (mock)
   const handleCreate = useCallback(async (table: string, data: any) => {
      console.log("Create:", table, data);
      // In real app, call API
      return { id: Date.now().toString(), ...data };
   }, []);

   const handleUpdate = useCallback(async (table: string, id: string, data: any) => {
      console.log("Update:", table, id, data);
      // In real app, call API
      return { id, ...data };
   }, []);

   const handleDelete = useCallback(async (table: string, id: string) => {
      console.log("Delete:", table, id);
      // In real app, call API
   }, []);

   const renderNavItem = (item: NavItem) => {
      const Icon = iconMap[item.icon?.toLowerCase() || "list"] || List;
      const isActive = activePage === item.name;

      return (
         <button
            key={item.name}
            onClick={() => {
               setActivePage(item.name);
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

   // If not V2 blueprint, show upgrade message
   if (!isV2) {
      return (
         <div className="min-h-screen bg-[#0a0a0f] flex items-center justify-center">
            <Card className="p-8 max-w-md text-center">
               <Database className="w-12 h-12 text-primary-400 mx-auto mb-4" />
               <h2 className="text-xl font-bold text-white mb-2">Legacy Blueprint</h2>
               <p className="text-white/60 mb-4">
                  This app uses Blueprint V1. Please regenerate to use the new dynamic UI system.
               </p>
               <Button onClick={() => window.history.back()}>Go Back</Button>
            </Card>
         </div>
      );
   }

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
               {navItems.map(renderNavItem)}
            </nav>
         </aside>

         {/* Main Content */}
         <main className={`transition-all ${sidebarOpen ? "ml-64" : "ml-0"}`}>
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
                     <span className="text-white">{currentPage?.title || "Home"}</span>
                  </div>
               </div>
            </header>

            {/* Page Content */}
            <div className="p-6">
               {currentPage ? (
                  <div>
                     <h2 className="text-2xl font-bold text-white mb-6">
                        {currentPage.title}
                     </h2>
                     <LayoutRenderer
                        layout={currentPage.layout}
                        blocks={currentPage.blocks}
                        data={mockData}
                        context={context}
                        onAction={handleAction}
                        onCreate={handleCreate}
                        onUpdate={handleUpdate}
                        onDelete={handleDelete}
                     />
                  </div>
               ) : (
                  <div className="text-center py-12 text-white/40">
                     <LayoutDashboard className="w-12 h-12 mx-auto mb-3 opacity-50" />
                     <p>No page selected</p>
                  </div>
               )}
            </div>
         </main>

         {/* Modal */}
         {currentModal && (
            <Modal
               isOpen={!!activeModal}
               onClose={() => setActiveModal(null)}
               title={currentModal.title}
               size={currentModal.size || "medium"}
            >
               <LayoutRenderer
                  blocks={currentModal.blocks}
                  data={mockData}
                  context={context}
                  onAction={handleAction}
                  onCreate={handleCreate}
                  onUpdate={handleUpdate}
                  onDelete={handleDelete}
               />
            </Modal>
         )}
      </div>
   );
}

