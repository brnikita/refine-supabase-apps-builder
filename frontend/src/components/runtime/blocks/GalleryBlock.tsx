"use client";

import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { X, ChevronLeft, ChevronRight, ZoomIn, Download, ExternalLink } from "lucide-react";
import { BlockComponentProps } from "./index";
import { GalleryProps } from "@/types/blueprint";

interface GalleryItem {
   id: string;
   [key: string]: any;
}

export function GalleryBlock({
   block,
   data,
   loading,
   onAction,
}: BlockComponentProps) {
   const props = block.props as GalleryProps;
   const [lightboxOpen, setLightboxOpen] = useState(false);
   const [lightboxIndex, setLightboxIndex] = useState(0);

   const aspectRatioClass = {
      "1:1": "aspect-square",
      "16:9": "aspect-video",
      "4:3": "aspect-[4/3]",
      "3:2": "aspect-[3/2]",
   }[props.aspectRatio || "1:1"];

   const columnsClass = {
      1: "grid-cols-1",
      2: "grid-cols-2",
      3: "grid-cols-3",
      4: "grid-cols-4",
      5: "grid-cols-5",
      6: "grid-cols-6",
   }[props.columns || 3] || "grid-cols-3";

   const handleItemClick = (item: GalleryItem, index: number) => {
      if (props.allowLightbox !== false) {
         setLightboxIndex(index);
         setLightboxOpen(true);
      }
      onAction?.("itemClick", { item, index }, { selectedRecord: item });
   };

   const handleLightboxNav = (direction: number) => {
      setLightboxIndex((prev) => {
         const newIndex = prev + direction;
         if (newIndex < 0) return data.length - 1;
         if (newIndex >= data.length) return 0;
         return newIndex;
      });
   };

   const handleKeyDown = (e: KeyboardEvent) => {
      if (!lightboxOpen) return;
      if (e.key === "Escape") setLightboxOpen(false);
      if (e.key === "ArrowLeft") handleLightboxNav(-1);
      if (e.key === "ArrowRight") handleLightboxNav(1);
   };

   // Add keyboard listener
   if (typeof window !== "undefined") {
      window.addEventListener("keydown", handleKeyDown);
   }

   if (loading) {
      return (
         <div className={`grid ${columnsClass} gap-4`}>
            {Array(6)
               .fill(0)
               .map((_, i) => (
                  <div
                     key={i}
                     className={`${aspectRatioClass} bg-white/5 rounded-lg animate-pulse`}
                  />
               ))}
         </div>
      );
   }

   if (!data || data.length === 0) {
      return (
         <Card className="p-12">
            <div className="text-center text-white/40">
               <ZoomIn className="w-12 h-12 mx-auto mb-3 opacity-50" />
               <p>No images to display</p>
            </div>
         </Card>
      );
   }

   const currentItem = data[lightboxIndex];

   return (
      <>
         {/* Gallery Grid */}
         <div className={`grid ${columnsClass} gap-4`}>
            {data.map((item: GalleryItem, index: number) => {
               const imageUrl = item[props.imageField];
               const title = props.titleField ? item[props.titleField] : null;
               const description = props.descriptionField
                  ? item[props.descriptionField]
                  : null;

               return (
                  <div
                     key={item.id || index}
                     className="group relative overflow-hidden rounded-lg bg-white/5 cursor-pointer"
                     onClick={() => handleItemClick(item, index)}
                  >
                     {/* Image */}
                     <div className={`${aspectRatioClass} overflow-hidden`}>
                        {imageUrl ? (
                           <img
                              src={imageUrl}
                              alt={title || "Gallery image"}
                              className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-110"
                           />
                        ) : (
                           <div className="w-full h-full flex items-center justify-center bg-white/5">
                              <ZoomIn className="w-8 h-8 text-white/20" />
                           </div>
                        )}
                     </div>

                     {/* Overlay */}
                     <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity">
                        <div className="absolute bottom-0 left-0 right-0 p-4">
                           {title && (
                              <h4 className="font-medium text-white truncate">{title}</h4>
                           )}
                           {description && (
                              <p className="text-sm text-white/70 line-clamp-2 mt-1">
                                 {description}
                              </p>
                           )}
                        </div>

                        {/* Zoom icon */}
                        <div className="absolute top-3 right-3">
                           <div className="w-8 h-8 rounded-full bg-black/50 flex items-center justify-center">
                              <ZoomIn className="w-4 h-4 text-white" />
                           </div>
                        </div>
                     </div>
                  </div>
               );
            })}
         </div>

         {/* Lightbox */}
         {lightboxOpen && currentItem && (
            <div
               className="fixed inset-0 z-50 bg-black/95 flex items-center justify-center"
               onClick={() => setLightboxOpen(false)}
            >
               {/* Close button */}
               <button
                  className="absolute top-4 right-4 p-2 rounded-full bg-white/10 text-white hover:bg-white/20 transition-colors z-10"
                  onClick={() => setLightboxOpen(false)}
               >
                  <X className="w-6 h-6" />
               </button>

               {/* Navigation */}
               {data.length > 1 && (
                  <>
                     <button
                        className="absolute left-4 top-1/2 -translate-y-1/2 p-3 rounded-full bg-white/10 text-white hover:bg-white/20 transition-colors z-10"
                        onClick={(e) => {
                           e.stopPropagation();
                           handleLightboxNav(-1);
                        }}
                     >
                        <ChevronLeft className="w-6 h-6" />
                     </button>
                     <button
                        className="absolute right-4 top-1/2 -translate-y-1/2 p-3 rounded-full bg-white/10 text-white hover:bg-white/20 transition-colors z-10"
                        onClick={(e) => {
                           e.stopPropagation();
                           handleLightboxNav(1);
                        }}
                     >
                        <ChevronRight className="w-6 h-6" />
                     </button>
                  </>
               )}

               {/* Image */}
               <div
                  className="max-w-[90vw] max-h-[85vh] relative"
                  onClick={(e) => e.stopPropagation()}
               >
                  <img
                     src={currentItem[props.imageField]}
                     alt={props.titleField ? currentItem[props.titleField] : ""}
                     className="max-w-full max-h-[85vh] object-contain"
                  />
               </div>

               {/* Caption */}
               <div className="absolute bottom-0 left-0 right-0 p-6 bg-gradient-to-t from-black/80 to-transparent">
                  <div className="max-w-3xl mx-auto text-center">
                     {props.titleField && currentItem[props.titleField] && (
                        <h3 className="text-xl font-medium text-white mb-2">
                           {currentItem[props.titleField]}
                        </h3>
                     )}
                     {props.descriptionField && currentItem[props.descriptionField] && (
                        <p className="text-white/70">
                           {currentItem[props.descriptionField]}
                        </p>
                     )}
                     <div className="flex items-center justify-center gap-4 mt-4">
                        <span className="text-white/40 text-sm">
                           {lightboxIndex + 1} / {data.length}
                        </span>
                     </div>
                  </div>
               </div>
            </div>
         )}
      </>
   );
}

