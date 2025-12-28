"use client";

import { cn } from "@/lib/utils";
import { HTMLAttributes, forwardRef } from "react";

interface CardProps extends HTMLAttributes<HTMLDivElement> {}

export const Card = forwardRef<HTMLDivElement, CardProps>(
   ({ className, children, ...props }, ref) => {
      return (
         <div
            ref={ref}
            className={cn(
               "gradient-card rounded-xl p-6",
               "transition-all duration-300",
               "hover:border-white/20",
               className
            )}
            {...props}
         >
            {children}
         </div>
      );
   }
);

Card.displayName = "Card";

