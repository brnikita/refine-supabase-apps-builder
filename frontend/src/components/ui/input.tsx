"use client";

import { cn } from "@/lib/utils";
import { forwardRef, InputHTMLAttributes } from "react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
   label?: string;
   error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
   ({ className, label, error, ...props }, ref) => {
      return (
         <div className="w-full">
            {label && (
               <label className="block text-sm font-medium text-white/80 mb-1.5">
                  {label}
               </label>
            )}
            <input
               ref={ref}
               className={cn(
                  "w-full px-4 py-2.5 rounded-lg",
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

Input.displayName = "Input";

