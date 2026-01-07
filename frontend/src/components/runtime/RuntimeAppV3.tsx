"use client";

import { useState, useMemo, useCallback } from "react";
import { Refine } from "@refinedev/core";
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
import { BlueprintV3, PageSpec, ModalSpec, NavItem, getEntityFromDataSource, normalizeBlockType } from "@/types/blueprint";
import { LayoutRenderer } from "./LayoutRenderer";
import { createAmplicationDataProvider, toApiResource } from "@/lib/amplicationDataProvider";

interface RuntimeAppV3Props {
   app: { id: string; name: string; slug: string };
   blueprint: BlueprintV3;
   runtimeConfig: { 
      db_schema: string; 
      base_path: string;
      backend_url?: string;  // V3: URL to generated backend
      backend_port?: number;
   };
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
   folder: FolderTree,
};

export function RuntimeAppV3({ app, blueprint, runtimeConfig }: RuntimeAppV3Props) {
   const [sidebarOpen, setSidebarOpen] = useState(true);
   const [activePage, setActivePage] = useState<string>(
      blueprint.ui?.pages?.[0]?.id || ""
   );
   const [activeModal, setActiveModal] = useState<string | null>(null);
   const [pageVariables, setPageVariables] = useState<Record<string, any>>({});
   const [selectedRecord, setSelectedRecord] = useState<any>(null);

   // Create data provider for the generated backend
   const dataProvider = useMemo(() => {
      const backendUrl = runtimeConfig.backend_url || `http://localhost:${runtimeConfig.backend_port || 4001}/api`;
      return createAmplicationDataProvider({ apiUrl: backendUrl });
   }, [runtimeConfig]);

   // Get resources from blueprint entities
   const resources = useMemo(() => {
      return blueprint.data.tables.map((table) => ({
         name: toApiResource(table.name),
         meta: {
            entity: table.name,
            displayName: table.displayName || table.name,
         },
      }));
   }, [blueprint]);

   // Get current page
   const currentPage = useMemo(() => {
      return blueprint.ui?.pages?.find((p: PageSpec) => p.id === activePage) || null;
   }, [blueprint, activePage]);

   // Get current modal
   const currentModal = useMemo(() => {
      if (!activeModal) return null;
      return blueprint.ui?.modals?.find((m: ModalSpec) => m.id === activeModal) || null;
   }, [blueprint, activeModal]);

   // Navigation items from pages
   const navItems = useMemo(() => {
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
   }, [blueprint]);

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

   // CRUD operations using Refine hooks (these will be passed to blocks)
   const handleCreate = useCallback(async (entity: string, data: any) => {
      const resource = toApiResource(entity);
      const response = await dataProvider.create({
         resource,
         variables: data,
      });
      return response.data;
   }, [dataProvider]);

   const handleUpdate = useCallback(async (entity: string, id: string, data: any) => {
      const resource = toApiResource(entity);
      const response = await dataProvider.update({
         resource,
         id,
         variables: data,
      });
      return response.data;
   }, [dataProvider]);

   const handleDelete = useCallback(async (entity: string, id: string) => {
      const resource = toApiResource(entity);
      await dataProvider.deleteOne({
         resource,
         id,
      });
   }, [dataProvider]);

   // Fetch data for blocks
   const fetchData = useCallback(async (entity: string, options?: { 
      page?: number; 
      pageSize?: number;
      sort?: { field: string; order: 'asc' | 'desc' };
      filters?: Array<{ field: string; value: any }>;
   }) => {
      const resource = toApiResource(entity);
      const response = await dataProvider.getList({
         resource,
         pagination: {
            current: options?.page || 1,
            pageSize: options?.pageSize || 10,
         },
         sorters: options?.sort ? [options.sort] : undefined,
         filters: options?.filters?.map(f => ({
            field: f.field,
            operator: "eq" as const,
            value: f.value,
         })),
      });
      return response;
   }, [dataProvider]);

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

   // Create data object for blocks (fetched from API)
   const [blockData, setBlockData] = useState<Record<string, any[]>>({});
   
   // Load data for current page blocks
   useMemo(() => {
      if (!currentPage) return;
      
      currentPage.blocks.forEach(async (block) => {
         const entity = getEntityFromDataSource(block.dataSource);
         if (entity && !blockData[entity]) {
            try {
               const result = await fetchData(entity);
               setBlockData(prev => ({
                  ...prev,
                  [entity]: result.data,
               }));
            } catch (error) {
               console.error(`Failed to fetch data for ${entity}:`, error);
            }
         }
      });
   }, [currentPage, fetchData]);

   return (
      <Refine
         dataProvider={dataProvider}
         resources={resources}
         options={{
            syncWithLocation: false,
            warnWhenUnsavedChanges: false,
         }}
      >
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
                  {/* V3 Badge */}
                  <div className="mt-2 flex items-center gap-2">
                     <span className="px-2 py-0.5 text-xs bg-green-500/20 text-green-400 rounded-full border border-green-500/30">
                        V3 Full-Stack
                     </span>
                     {runtimeConfig.backend_url && (
                        <span className="px-2 py-0.5 text-xs bg-blue-500/20 text-blue-400 rounded-full border border-blue-500/30">
                           API Connected
                        </span>
                     )}
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
                           data={blockData}
                           context={context}
                           onAction={handleAction}
                           onCreate={handleCreate}
                           onUpdate={handleUpdate}
                           onDelete={handleDelete}
                           fetchData={fetchData}
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
                     data={blockData}
                     context={context}
                     onAction={handleAction}
                     onCreate={handleCreate}
                     onUpdate={handleUpdate}
                     onDelete={handleDelete}
                     fetchData={fetchData}
                  />
               </Modal>
            )}
         </div>
      </Refine>
   );
}

