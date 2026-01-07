"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getRuntimeApp } from "@/lib/api";
import { Loader2, AlertCircle, Power } from "lucide-react";
import { RuntimeAppV2 } from "@/components/runtime/RuntimeAppV2";
import { RuntimeAppV3 } from "@/components/runtime/RuntimeAppV3";
import { isBlueprintV2, isBlueprintV3, BlueprintV2, BlueprintV3 } from "@/types/blueprint";

interface RuntimeData {
   status: string;
   app?: { id: string; name: string; slug: string };
   runtime_config?: { 
      db_schema: string; 
      base_path: string;
      backend_url?: string;
      backend_port?: number;
   };
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

   // Check blueprint version and render appropriate runtime
   const blueprint = runtimeData.blueprint;

   // V3 Blueprint - Full-stack with generated backend
   if (isBlueprintV3(blueprint)) {
      return (
         <RuntimeAppV3
            app={runtimeData.app!}
            blueprint={blueprint as BlueprintV3}
            runtimeConfig={runtimeData.runtime_config!}
         />
      );
   }

   // V2 Blueprint - Legacy with mock data
   if (isBlueprintV2(blueprint)) {
      return (
         <RuntimeAppV2
            app={runtimeData.app!}
            blueprint={blueprint as BlueprintV2}
            runtimeConfig={runtimeData.runtime_config!}
         />
      );
   }

   // Invalid blueprint
   return (
      <div className="min-h-screen gradient-bg flex items-center justify-center">
         <div className="text-center">
            <AlertCircle className="w-16 h-16 text-amber-400 mx-auto mb-4" />
            <h1 className="text-2xl font-bold text-white mb-2">Invalid Blueprint</h1>
            <p className="text-white/60">This app has an invalid or outdated blueprint format.</p>
            <p className="text-white/40 text-sm mt-2">
               Blueprint version: {blueprint?.version || "unknown"}
            </p>
         </div>
      </div>
   );
}
