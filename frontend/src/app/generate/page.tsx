"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card } from "@/components/ui/card";
import { generateApp, getJob, getMe } from "@/lib/api";
import {
   ArrowLeft,
   Sparkles,
   Loader2,
   CheckCircle,
   XCircle,
   Lightbulb,
} from "lucide-react";

const EXAMPLE_PROMPTS = [
   "A task management app with projects, tasks, and team members. Users can create projects, add tasks with due dates and priorities, and assign them to team members.",
   "An inventory management system for a small retail store. Track products, stock levels, suppliers, and purchase orders.",
   "A simple CRM for a consulting firm. Manage clients, contacts, deals, and meeting notes.",
   "A booking system for a fitness studio. Manage classes, instructors, and member reservations.",
];

export default function GeneratePage() {
   const router = useRouter();
   const [prompt, setPrompt] = useState("");
   const [generating, setGenerating] = useState(false);
   const [jobId, setJobId] = useState<string | null>(null);
   const [jobStatus, setJobStatus] = useState<string | null>(null);
   const [error, setError] = useState<string | null>(null);

   useEffect(() => {
      const checkAuth = async () => {
         const { data, error } = await getMe();
         if (error || !data) {
            router.push("/");
         }
      };
      checkAuth();
   }, [router]);

   useEffect(() => {
      if (!jobId) return;

      const pollJob = async () => {
         const { data, error } = await getJob(jobId);
         if (error) {
            setError(error);
            setGenerating(false);
            return;
         }

         if (data) {
            setJobStatus(data.status);

            if (data.status === "SUCCEEDED") {
               setGenerating(false);
               // Redirect to dashboard after a short delay
               setTimeout(() => {
                  router.push("/dashboard");
               }, 1500);
            } else if (data.status === "FAILED") {
               setError(data.error_message || "Generation failed");
               setGenerating(false);
            } else if (data.status === "RUNNING" || data.status === "QUEUED") {
               // Continue polling
               setTimeout(pollJob, 2000);
            }
         }
      };

      pollJob();
   }, [jobId, router]);

   const handleGenerate = async () => {
      if (!prompt.trim()) return;

      setGenerating(true);
      setError(null);
      setJobStatus("QUEUED");

      const { data, error } = await generateApp(prompt);

      if (error) {
         setError(error);
         setGenerating(false);
         return;
      }

      if (data) {
         setJobId(data.job_id);
      }
   };

   const useExample = (example: string) => {
      setPrompt(example);
   };

   return (
      <div className="min-h-screen gradient-bg">
         {/* Background decoration */}
         <div className="absolute inset-0 overflow-hidden pointer-events-none">
            <div className="absolute top-20 left-1/4 w-72 h-72 bg-primary-500/10 rounded-full blur-3xl" />
            <div className="absolute bottom-20 right-1/4 w-72 h-72 bg-accent-500/10 rounded-full blur-3xl" />
         </div>

         <div className="relative z-10 container mx-auto px-4 py-8">
            {/* Back button */}
            <Button
               variant="ghost"
               onClick={() => router.push("/dashboard")}
               className="mb-8"
            >
               <ArrowLeft className="w-4 h-4 mr-2" />
               Back to Dashboard
            </Button>

            <div className="max-w-3xl mx-auto">
               {/* Header */}
               <div className="text-center mb-8">
                  <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl gradient-button mb-4">
                     <Sparkles className="w-8 h-8 text-white" />
                  </div>
                  <h1 className="text-3xl font-bold text-white mb-2">
                     Generate New App
                  </h1>
                  <p className="text-white/60">
                     Describe the business application you want to create
                  </p>
               </div>

               {/* Main Form */}
               <Card className="mb-6">
                  <Textarea
                     label="App Description"
                     placeholder="Describe your business application in detail. Include the main entities, relationships, and features you need..."
                     value={prompt}
                     onChange={(e) => setPrompt(e.target.value)}
                     rows={6}
                     disabled={generating}
                  />

                  {/* Generation Status */}
                  {generating && (
                     <div className="mt-4 p-4 rounded-lg bg-white/5 border border-white/10">
                        <div className="flex items-center gap-3">
                           {jobStatus === "SUCCEEDED" ? (
                              <CheckCircle className="w-5 h-5 text-emerald-400" />
                           ) : (
                              <Loader2 className="w-5 h-5 text-primary-400 animate-spin" />
                           )}
                           <div>
                              <p className="text-white font-medium">
                                 {jobStatus === "QUEUED" && "Queued..."}
                                 {jobStatus === "RUNNING" && "Generating your app..."}
                                 {jobStatus === "SUCCEEDED" && "App created successfully!"}
                              </p>
                              <p className="text-white/50 text-sm">
                                 {jobStatus === "RUNNING" &&
                                    "This may take a minute. We're creating tables, permissions, and UI..."}
                                 {jobStatus === "SUCCEEDED" &&
                                    "Redirecting to dashboard..."}
                              </p>
                           </div>
                        </div>
                     </div>
                  )}

                  {/* Error */}
                  {error && (
                     <div className="mt-4 p-4 rounded-lg bg-red-500/10 border border-red-500/20">
                        <div className="flex items-center gap-3">
                           <XCircle className="w-5 h-5 text-red-400" />
                           <div>
                              <p className="text-red-400 font-medium">Generation Failed</p>
                              <p className="text-red-400/70 text-sm">{error}</p>
                           </div>
                        </div>
                     </div>
                  )}

                  <div className="mt-4 flex justify-end">
                     <Button
                        onClick={handleGenerate}
                        disabled={!prompt.trim() || generating}
                        loading={generating}
                        size="lg"
                     >
                        <Sparkles className="w-4 h-4 mr-2" />
                        Generate App
                     </Button>
                  </div>
               </Card>

               {/* Example Prompts */}
               <div>
                  <div className="flex items-center gap-2 mb-4">
                     <Lightbulb className="w-5 h-5 text-amber-400" />
                     <h3 className="text-lg font-medium text-white">Example Prompts</h3>
                  </div>

                  <div className="grid gap-3">
                     {EXAMPLE_PROMPTS.map((example, index) => (
                        <button
                           key={index}
                           onClick={() => useExample(example)}
                           disabled={generating}
                           className="text-left p-4 rounded-lg bg-white/5 border border-white/10 hover:bg-white/10 hover:border-white/20 transition-all text-white/70 hover:text-white disabled:opacity-50"
                        >
                           {example}
                        </button>
                     ))}
                  </div>
               </div>
            </div>
         </div>
      </div>
   );
}

