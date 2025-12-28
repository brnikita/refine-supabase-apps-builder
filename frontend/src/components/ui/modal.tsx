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
}

export function Modal({ isOpen, onClose, title, children, className }: ModalProps) {
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
               "relative z-10 w-full max-w-md mx-4",
               "gradient-card rounded-2xl p-6",
               "animate-fade-in",
               className
            )}
         >
            {/* Header */}
            {title && (
               <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold text-white">{title}</h2>
                  <button
                     onClick={onClose}
                     className="p-1 rounded-lg text-white/60 hover:text-white hover:bg-white/10 transition-colors"
                  >
                     <X className="w-5 h-5" />
                  </button>
               </div>
            )}

            {/* Content */}
            {children}
         </div>
      </div>
   );
}

