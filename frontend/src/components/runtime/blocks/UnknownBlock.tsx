"use client";

import { AlertCircle } from "lucide-react";
import { Card } from "@/components/ui/card";
import { BlockComponentProps } from "./index";

export function UnknownBlock({ block }: BlockComponentProps) {
   return (
      <Card className="p-6 border-dashed border-yellow-500/50 bg-yellow-500/5">
         <div className="flex items-center gap-3 text-yellow-500">
            <AlertCircle className="w-5 h-5" />
            <div>
               <p className="font-medium">Unknown Block Type: {block.type}</p>
               <p className="text-sm text-white/60 mt-1">
                  This block type is not yet implemented. Block ID: {block.id}
               </p>
            </div>
         </div>
      </Card>
   );
}

