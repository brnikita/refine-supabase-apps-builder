"use client";

import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { BlockComponentProps } from "./index";
import { FormProps, FormFieldDef } from "@/types/blueprint";

export function FormBlock({
   block,
   data,
   onCreate,
   onUpdate,
   onAction,
   context,
}: BlockComponentProps) {
   const props = block.props as FormProps;
   const isEdit = props.mode === "edit";
   const record = context?.selectedRecord || (data && data[0]);

   const [formData, setFormData] = useState<Record<string, any>>(() => {
      if (isEdit && record) {
         return { ...record };
      }
      // Initialize with default values
      const defaults: Record<string, any> = {};
      props.fields?.forEach((field) => {
         if (field.defaultValue !== undefined) {
            defaults[field.name] = field.defaultValue;
         }
      });
      return defaults;
   });

   const [errors, setErrors] = useState<Record<string, string>>({});
   const [submitting, setSubmitting] = useState(false);

   const handleChange = (name: string, value: any) => {
      setFormData((prev) => ({ ...prev, [name]: value }));
      // Clear error when field is modified
      if (errors[name]) {
         setErrors((prev) => {
            const next = { ...prev };
            delete next[name];
            return next;
         });
      }
   };

   const validate = (): boolean => {
      const newErrors: Record<string, string> = {};
      props.fields?.forEach((field) => {
         if (field.required && !formData[field.name]) {
            newErrors[field.name] = `${field.label} is required`;
         }
      });
      setErrors(newErrors);
      return Object.keys(newErrors).length === 0;
   };

   const handleSubmit = async (e: React.FormEvent) => {
      e.preventDefault();
      if (!validate()) return;

      setSubmitting(true);
      try {
         if (isEdit && record?.id) {
            await onUpdate?.(record.id, formData);
         } else {
            await onCreate?.(formData);
         }
         onAction?.("submit", { data: formData }, context);
      } catch (error) {
         console.error("Form submission error:", error);
      } finally {
         setSubmitting(false);
      }
   };

   const handleCancel = () => {
      onAction?.("cancel", {}, context);
   };

   const renderField = (field: FormFieldDef) => {
      const value = formData[field.name] ?? "";
      const error = errors[field.name];

      const baseInputClass = `w-full px-4 py-2.5 rounded-lg bg-white/5 border text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-primary-500/50 ${
         error ? "border-red-500" : "border-white/10"
      }`;

      switch (field.type) {
         case "textarea":
            return (
               <Textarea
                  value={value}
                  onChange={(e) => handleChange(field.name, e.target.value)}
                  placeholder={field.placeholder || `Enter ${field.label.toLowerCase()}`}
                  className={baseInputClass}
                  rows={4}
               />
            );

         case "select":
            return (
               <select
                  value={value}
                  onChange={(e) => handleChange(field.name, e.target.value)}
                  className={baseInputClass}
               >
                  <option value="">Select {field.label}...</option>
                  {field.options?.map((opt) => {
                     const optValue = typeof opt === "string" ? opt : opt.value;
                     const optLabel = typeof opt === "string" ? opt : opt.label;
                     return (
                        <option key={optValue} value={optValue}>
                           {optLabel}
                        </option>
                     );
                  })}
               </select>
            );

         case "checkbox":
            return (
               <label className="flex items-center gap-3 cursor-pointer">
                  <input
                     type="checkbox"
                     checked={!!value}
                     onChange={(e) => handleChange(field.name, e.target.checked)}
                     className="w-5 h-5 rounded bg-white/5 border border-white/10 text-primary-500 focus:ring-primary-500/50"
                  />
                  <span className="text-white/80">{field.placeholder || "Enable"}</span>
               </label>
            );

         case "date":
            return (
               <Input
                  type="date"
                  value={value ? value.split("T")[0] : ""}
                  onChange={(e) => handleChange(field.name, e.target.value)}
                  className={baseInputClass}
               />
            );

         case "datetime":
            return (
               <Input
                  type="datetime-local"
                  value={value ? value.slice(0, 16) : ""}
                  onChange={(e) => handleChange(field.name, e.target.value)}
                  className={baseInputClass}
               />
            );

         case "number":
            return (
               <Input
                  type="number"
                  value={value}
                  onChange={(e) => handleChange(field.name, parseFloat(e.target.value) || 0)}
                  placeholder={field.placeholder || `Enter ${field.label.toLowerCase()}`}
                  className={baseInputClass}
               />
            );

         case "email":
            return (
               <Input
                  type="email"
                  value={value}
                  onChange={(e) => handleChange(field.name, e.target.value)}
                  placeholder={field.placeholder || "email@example.com"}
                  className={baseInputClass}
               />
            );

         case "password":
            return (
               <Input
                  type="password"
                  value={value}
                  onChange={(e) => handleChange(field.name, e.target.value)}
                  placeholder={field.placeholder || "••••••••"}
                  className={baseInputClass}
               />
            );

         case "url":
            return (
               <Input
                  type="url"
                  value={value}
                  onChange={(e) => handleChange(field.name, e.target.value)}
                  placeholder={field.placeholder || "https://"}
                  className={baseInputClass}
               />
            );

         case "color":
            return (
               <div className="flex items-center gap-3">
                  <input
                     type="color"
                     value={value || "#6366f1"}
                     onChange={(e) => handleChange(field.name, e.target.value)}
                     className="w-12 h-10 rounded cursor-pointer bg-transparent"
                  />
                  <Input
                     type="text"
                     value={value}
                     onChange={(e) => handleChange(field.name, e.target.value)}
                     placeholder="#000000"
                     className={`${baseInputClass} flex-1`}
                  />
               </div>
            );

         case "relation":
            // For relation fields, we'd normally fetch related data
            // For now, show a simple select
            return (
               <select
                  value={value}
                  onChange={(e) => handleChange(field.name, e.target.value)}
                  className={baseInputClass}
               >
                  <option value="">Select {field.label}...</option>
                  {/* Related options would be loaded here */}
               </select>
            );

         case "file":
            return (
               <Input
                  type="file"
                  onChange={(e) => {
                     const file = e.target.files?.[0];
                     if (file) handleChange(field.name, file);
                  }}
                  className={baseInputClass}
               />
            );

         default:
            return (
               <Input
                  type="text"
                  value={value}
                  onChange={(e) => handleChange(field.name, e.target.value)}
                  placeholder={field.placeholder || `Enter ${field.label.toLowerCase()}`}
                  className={baseInputClass}
               />
            );
      }
   };

   return (
      <Card className="p-6">
         <form onSubmit={handleSubmit} className="space-y-5">
            {props.fields?.map((field) => (
               <div key={field.name}>
                  <label className="block text-sm font-medium text-white/80 mb-1.5">
                     {field.label}
                     {field.required && <span className="text-red-400 ml-1">*</span>}
                  </label>
                  {renderField(field)}
                  {errors[field.name] && (
                     <p className="mt-1 text-sm text-red-400">{errors[field.name]}</p>
                  )}
               </div>
            ))}

            <div className="flex gap-3 pt-4">
               <Button type="submit" disabled={submitting}>
                  {submitting ? "Saving..." : props.submitLabel || (isEdit ? "Save Changes" : "Create")}
               </Button>
               <Button type="button" variant="secondary" onClick={handleCancel}>
                  {props.cancelLabel || "Cancel"}
               </Button>
            </div>
         </form>
      </Card>
   );
}

