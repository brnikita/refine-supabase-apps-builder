"use client";

import { cn } from "@/lib/utils";
import { X } from "lucide-react";
import { useEffect, useCallback } from "react";

interface ModalProps {
   isOpen: boolean;
   onClose: () => void;
   title?: string;
   children: React.ReactNode;
   className?: string;
   size?: "small" | "medium" | "large" | "fullscreen";
}

const sizeClasses = {
   small: "max-w-sm",
   medium: "max-w-lg",
   large: "max-w-3xl",
   fullscreen: "max-w-[95vw] max-h-[95vh]",
};

export function Modal({
   isOpen,
   onClose,
   title,
   children,
   className,
   size = "medium",
}: ModalProps) {
   const handleEscape = useCallback(
      (e: KeyboardEvent) => {
         if (e.key === "Escape") {
            onClose();
         }
      },
      [onClose]
   );

   useEffect(() => {
      if (isOpen) {
         document.addEventListener("keydown", handleEscape);
         document.body.style.overflow = "hidden";
      }
      return () => {
         document.removeEventListener("keydown", handleEscape);
         document.body.style.overflow = "unset";
      };
   }, [isOpen, handleEscape]);

   if (!isOpen) return null;

   return (
      <div className="fixed inset-0 z-50 flex items-center justify-center">
         {/* Backdrop */}
         <div
            className="absolute inset-0 bg-black/70 backdrop-blur-sm"
            onClick={onClose}
         />

         {/* Modal */}
         <div
            className={cn(
               "relative z-10 w-full mx-4",
               sizeClasses[size],
               size === "fullscreen" ? "h-[95vh] overflow-auto" : "",
               "gradient-card rounded-2xl p-6",
               "animate-fade-in",
               className
            )}
         >
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
               {title && <h2 className="text-lg font-semibold text-white">{title}</h2>}
               <button
                  onClick={onClose}
                  className="p-1 rounded-lg text-white/60 hover:text-white hover:bg-white/10 transition-colors ml-auto"
               >
                  <X className="w-5 h-5" />
               </button>
            </div>

            {/* Content */}
            <div className={size === "fullscreen" ? "overflow-auto" : ""}>
               {children}
            </div>
         </div>
      </div>
   );
}
