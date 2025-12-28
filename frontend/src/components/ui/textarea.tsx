"use client";

import { cn } from "@/lib/utils";
import { forwardRef, TextareaHTMLAttributes } from "react";

interface TextareaProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
   label?: string;
   error?: string;
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
   ({ className, label, error, ...props }, ref) => {
      return (
         <div className="w-full">
            {label && (
               <label className="block text-sm font-medium text-white/80 mb-1.5">
                  {label}
               </label>
            )}
            <textarea
               ref={ref}
               className={cn(
                  "w-full px-4 py-3 rounded-lg resize-none",
                  "bg-white/5 border border-white/10",
                  "text-white placeholder-white/40",
                  "focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500/50",
                  "transition-all duration-200",
                  error && "border-red-500/50 focus:ring-red-500/50",
                  className
               )}
               {...props}
            />
            {error && <p className="mt-1 text-sm text-red-400">{error}</p>}
         </div>
      );
   }
);

Textarea.displayName = "Textarea";

