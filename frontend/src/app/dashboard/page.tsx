"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Modal } from "@/components/ui/modal";
import {
   listApps,
   startApp,
   stopApp,
   deleteApp,
   getMe,
   logout,
   App,
} from "@/lib/api";
import {
   Plus,
   Play,
   Square,
   Trash2,
   ExternalLink,
   LogOut,
   Loader2,
   Box,
   Sparkles,
} from "lucide-react";

export default function Dashboard() {
   const router = useRouter();
   const [apps, setApps] = useState<App[]>([]);
   const [loading, setLoading] = useState(true);
   const [userEmail, setUserEmail] = useState("");
   const [deleteModal, setDeleteModal] = useState<{ isOpen: boolean; app?: App }>({
      isOpen: false,
   });
   const [actionLoading, setActionLoading] = useState<string | null>(null);

   useEffect(() => {
      const init = async () => {
         const { data: user, error } = await getMe();
         if (error || !user) {
            router.push("/");
            return;
         }
         setUserEmail(user.email);
         await loadApps();
      };
      init();
   }, [router]);

   const loadApps = async () => {
      setLoading(true);
      const { data, error } = await listApps();
      if (data) {
         setApps(data.apps);
      }
      setLoading(false);
   };

   const handleStart = async (appId: string) => {
      setActionLoading(appId);
      await startApp(appId);
      await loadApps();
      setActionLoading(null);
   };

   const handleStop = async (appId: string) => {
      setActionLoading(appId);
      await stopApp(appId);
      await loadApps();
      setActionLoading(null);
   };

   const handleDelete = async () => {
      if (!deleteModal.app) return;
      setActionLoading(deleteModal.app.id);
      await deleteApp(deleteModal.app.id);
      setDeleteModal({ isOpen: false });
      await loadApps();
      setActionLoading(null);
   };

   const handleLogout = () => {
      logout();
      router.push("/");
   };

   const getStatusBadge = (status: App["status"]) => {
      const variants: Record<App["status"], "success" | "warning" | "error" | "info" | "default"> = {
         RUNNING: "success",
         STOPPED: "warning",
         DRAFT: "info",
         ERROR: "error",
         DELETING: "default",
      };
      return <Badge variant={variants[status]}>{status}</Badge>;
   };

   const formatDate = (dateString: string) => {
      return new Date(dateString).toLocaleDateString("en-US", {
         month: "short",
         day: "numeric",
         year: "numeric",
         hour: "2-digit",
         minute: "2-digit",
      });
   };

   return (
      <div className="min-h-screen gradient-bg">
         {/* Background decoration */}
         <div className="absolute inset-0 overflow-hidden pointer-events-none">
            <div className="absolute top-0 right-0 w-96 h-96 bg-primary-500/10 rounded-full blur-3xl" />
            <div className="absolute bottom-0 left-0 w-96 h-96 bg-accent-500/10 rounded-full blur-3xl" />
         </div>

         <div className="relative z-10">
            {/* Header */}
            <header className="border-b border-white/10 bg-black/20 backdrop-blur-sm">
               <div className="container mx-auto px-4 py-4 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                     <div className="w-10 h-10 rounded-xl gradient-button flex items-center justify-center">
                        <Sparkles className="w-5 h-5 text-white" />
                     </div>
                     <span className="text-xl font-semibold text-white">Blueprint Apps</span>
                  </div>

                  <div className="flex items-center gap-4">
                     <span className="text-white/60 text-sm">{userEmail}</span>
                     <Button variant="ghost" size="sm" onClick={handleLogout}>
                        <LogOut className="w-4 h-4 mr-2" />
                        Logout
                     </Button>
                  </div>
               </div>
            </header>

            {/* Main Content */}
            <main className="container mx-auto px-4 py-8">
               {/* Page Header */}
               <div className="flex items-center justify-between mb-8">
                  <div>
                     <h1 className="text-3xl font-bold text-white mb-2">Your Apps</h1>
                     <p className="text-white/60">
                        Manage your generated business applications
                     </p>
                  </div>

                  <Button onClick={() => router.push("/generate")} size="lg">
                     <Plus className="w-5 h-5 mr-2" />
                     Generate New App
                  </Button>
               </div>

               {/* Apps Grid */}
               {loading ? (
                  <div className="flex items-center justify-center py-20">
                     <Loader2 className="w-8 h-8 text-white/60 animate-spin" />
                  </div>
               ) : apps.length === 0 ? (
                  <Card className="text-center py-16">
                     <Box className="w-16 h-16 text-white/20 mx-auto mb-4" />
                     <h3 className="text-xl font-medium text-white mb-2">No apps yet</h3>
                     <p className="text-white/60 mb-6">
                        Generate your first business app with AI
                     </p>
                     <Button onClick={() => router.push("/generate")}>
                        <Plus className="w-4 h-4 mr-2" />
                        Generate App
                     </Button>
                  </Card>
               ) : (
                  <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                     {apps.map((app) => (
                        <Card key={app.id} className="group">
                           <div className="flex items-start justify-between mb-4">
                              <div>
                                 <h3 className="text-lg font-semibold text-white mb-1">
                                    {app.name}
                                 </h3>
                                 <p className="text-white/50 text-sm font-mono">
                                    /{app.slug}
                                 </p>
                              </div>
                              {getStatusBadge(app.status)}
                           </div>

                           <p className="text-white/40 text-sm mb-4">
                              Created {formatDate(app.created_at)}
                           </p>

                           <div className="flex items-center gap-2">
                              {app.status === "RUNNING" && (
                                 <>
                                    <Button
                                       variant="secondary"
                                       size="sm"
                                       onClick={() => window.open(`/apps/${app.slug}`, "_blank")}
                                    >
                                       <ExternalLink className="w-4 h-4 mr-1" />
                                       Open
                                    </Button>
                                    <Button
                                       variant="ghost"
                                       size="sm"
                                       onClick={() => handleStop(app.id)}
                                       loading={actionLoading === app.id}
                                    >
                                       <Square className="w-4 h-4 mr-1" />
                                       Stop
                                    </Button>
                                 </>
                              )}

                              {app.status === "STOPPED" && (
                                 <Button
                                    variant="secondary"
                                    size="sm"
                                    onClick={() => handleStart(app.id)}
                                    loading={actionLoading === app.id}
                                 >
                                    <Play className="w-4 h-4 mr-1" />
                                    Start
                                 </Button>
                              )}

                              {app.status !== "DELETING" && (
                                 <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => setDeleteModal({ isOpen: true, app })}
                                    className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
                                 >
                                    <Trash2 className="w-4 h-4" />
                                 </Button>
                              )}
                           </div>
                        </Card>
                     ))}
                  </div>
               )}
            </main>
         </div>

         {/* Delete Confirmation Modal */}
         <Modal
            isOpen={deleteModal.isOpen}
            onClose={() => setDeleteModal({ isOpen: false })}
            title="Delete App"
         >
            <p className="text-white/70 mb-6">
               Are you sure you want to delete{" "}
               <span className="text-white font-medium">{deleteModal.app?.name}</span>?
               This action cannot be undone.
            </p>
            <div className="flex gap-3 justify-end">
               <Button
                  variant="secondary"
                  onClick={() => setDeleteModal({ isOpen: false })}
               >
                  Cancel
               </Button>
               <Button
                  variant="danger"
                  onClick={handleDelete}
                  loading={actionLoading === deleteModal.app?.id}
               >
                  Delete
               </Button>
            </div>
         </Modal>
      </div>
   );
}

