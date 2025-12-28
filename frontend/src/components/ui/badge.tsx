"use client";

import { cn } from "@/lib/utils";
import { HTMLAttributes } from "react";

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
   variant?: "default" | "success" | "warning" | "error" | "info";
}

export function Badge({ className, variant = "default", children, ...props }: BadgeProps) {
   const variants = {
      default: "bg-white/10 text-white/80",
      success: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30",
      warning: "bg-amber-500/20 text-amber-400 border-amber-500/30",
      error: "bg-red-500/20 text-red-400 border-red-500/30",
      info: "bg-blue-500/20 text-blue-400 border-blue-500/30",
   };

   return (
      <span
         className={cn(
            "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border",
            variants[variant],
            className
         )}
         {...props}
      >
         {children}
      </span>
   );
}

