"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getRuntimeApp } from "@/lib/api";
import { Loader2, AlertCircle, Power } from "lucide-react";
import { RuntimeApp } from "@/components/runtime/RuntimeApp";
import { RuntimeAppV2 } from "@/components/runtime/RuntimeAppV2";
import { isBlueprintV2 } from "@/types/blueprint";

interface RuntimeData {
   status: string;
   app?: { id: string; name: string; slug: string };
   runtime_config?: { db_schema: string; base_path: string };
   blueprint?: any;
   message?: string;
}

export default function AppRuntimePage() {
   const params = useParams();
   const slug = params.slug as string;
   const [loading, setLoading] = useState(true);
   const [error, setError] = useState<string | null>(null);
   const [runtimeData, setRuntimeData] = useState<RuntimeData | null>(null);

   useEffect(() => {
      const loadApp = async () => {
         setLoading(true);
         const { data, error } = await getRuntimeApp(slug);

         if (error) {
            setError(error);
         } else if (data) {
            setRuntimeData(data);
         }
         setLoading(false);
      };

      loadApp();
   }, [slug]);

   if (loading) {
      return (
         <div className="min-h-screen gradient-bg flex items-center justify-center">
            <div className="text-center">
               <Loader2 className="w-12 h-12 text-white/60 animate-spin mx-auto mb-4" />
               <p className="text-white/60">Loading application...</p>
            </div>
         </div>
      );
   }

   if (error) {
      return (
         <div className="min-h-screen gradient-bg flex items-center justify-center">
            <div className="text-center">
               <AlertCircle className="w-16 h-16 text-red-400 mx-auto mb-4" />
               <h1 className="text-2xl font-bold text-white mb-2">App Not Found</h1>
               <p className="text-white/60">{error}</p>
            </div>
         </div>
      );
   }

   if (runtimeData?.status === "stopped") {
      return (
         <div className="min-h-screen gradient-bg flex items-center justify-center">
            <div className="text-center">
               <Power className="w-16 h-16 text-amber-400 mx-auto mb-4" />
               <h1 className="text-2xl font-bold text-white mb-2">App Stopped</h1>
               <p className="text-white/60">{runtimeData.message}</p>
            </div>
         </div>
      );
   }

   if (!runtimeData?.blueprint) {
      return (
         <div className="min-h-screen gradient-bg flex items-center justify-center">
            <div className="text-center">
               <AlertCircle className="w-16 h-16 text-amber-400 mx-auto mb-4" />
               <h1 className="text-2xl font-bold text-white mb-2">No Blueprint</h1>
               <p className="text-white/60">This app doesn't have a valid blueprint.</p>
            </div>
         </div>
      );
   }

   // Use V2 runtime if blueprint is version 2
   const isV2 = isBlueprintV2(runtimeData.blueprint);

   if (isV2) {
      return (
         <RuntimeAppV2
            app={runtimeData.app!}
            blueprint={runtimeData.blueprint}
            runtimeConfig={runtimeData.runtime_config!}
         />
      );
   }

   // Fall back to V1 runtime for legacy blueprints
   return (
      <RuntimeApp
         app={runtimeData.app!}
         blueprint={runtimeData.blueprint}
         runtimeConfig={runtimeData.runtime_config!}
      />
   );
}
