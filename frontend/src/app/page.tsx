"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { login, register, getMe } from "@/lib/api";
import { Sparkles, Zap, Shield, ArrowRight } from "lucide-react";

export default function Home() {
   const router = useRouter();
   const [isLogin, setIsLogin] = useState(true);
   const [email, setEmail] = useState("");
   const [password, setPassword] = useState("");
   const [loading, setLoading] = useState(false);
   const [error, setError] = useState("");
   const [checkingAuth, setCheckingAuth] = useState(true);

   useEffect(() => {
      // Check if already authenticated
      const checkAuth = async () => {
         const token = localStorage.getItem("token");
         if (token) {
            const { data } = await getMe();
            if (data) {
               router.push("/dashboard");
               return;
            }
         }
         setCheckingAuth(false);
      };
      checkAuth();
   }, [router]);

   const handleSubmit = async (e: React.FormEvent) => {
      e.preventDefault();
      setLoading(true);
      setError("");

      try {
         if (isLogin) {
            const { data, error } = await login(email, password);
            if (error) {
               setError(error);
            } else {
               router.push("/dashboard");
            }
         } else {
            const { data, error } = await register(email, password);
            if (error) {
               setError(error);
            } else {
               // Auto-login after registration
               const loginResult = await login(email, password);
               if (loginResult.error) {
                  setError(loginResult.error);
               } else {
                  router.push("/dashboard");
               }
            }
         }
      } finally {
         setLoading(false);
      }
   };

   if (checkingAuth) {
      return (
         <div className="min-h-screen gradient-bg flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-white"></div>
         </div>
      );
   }

   return (
      <div className="min-h-screen gradient-bg">
         {/* Background decoration */}
         <div className="absolute inset-0 overflow-hidden">
            <div className="absolute -top-40 -right-40 w-80 h-80 bg-primary-500/20 rounded-full blur-3xl" />
            <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-accent-500/20 rounded-full blur-3xl" />
         </div>

         <div className="relative z-10 container mx-auto px-4 py-16">
            {/* Hero Section */}
            <div className="text-center mb-16 animate-fade-in">
               <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/5 border border-white/10 mb-6">
                  <Sparkles className="w-4 h-4 text-accent-400" />
                  <span className="text-sm text-white/80">AI-Powered App Generation</span>
               </div>

               <h1 className="text-5xl md:text-7xl font-bold mb-6">
                  <span className="bg-gradient-to-r from-white via-primary-200 to-accent-300 bg-clip-text text-transparent">
                     Blueprint Apps
                  </span>
                  <br />
                  <span className="text-white/90">Builder</span>
               </h1>

               <p className="text-xl text-white/60 max-w-2xl mx-auto mb-8">
                  Generate complete business web applications from natural language descriptions.
                  Just describe what you need, and watch your app come to life.
               </p>

               {/* Features */}
               <div className="flex flex-wrap justify-center gap-6 mb-12">
                  <div className="flex items-center gap-2 text-white/70">
                     <Zap className="w-5 h-5 text-primary-400" />
                     <span>Instant Generation</span>
                  </div>
                  <div className="flex items-center gap-2 text-white/70">
                     <Shield className="w-5 h-5 text-emerald-400" />
                     <span>Built-in Security</span>
                  </div>
                  <div className="flex items-center gap-2 text-white/70">
                     <ArrowRight className="w-5 h-5 text-accent-400" />
                     <span>Ready to Deploy</span>
                  </div>
               </div>
            </div>

            {/* Auth Form */}
            <div className="max-w-md mx-auto animate-slide-up">
               <div className="gradient-card rounded-2xl p-8">
                  <h2 className="text-2xl font-semibold text-white mb-6 text-center">
                     {isLogin ? "Welcome Back" : "Create Account"}
                  </h2>

                  <form onSubmit={handleSubmit} className="space-y-4">
                     <Input
                        type="email"
                        label="Email"
                        placeholder="you@example.com"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                     />

                     <Input
                        type="password"
                        label="Password"
                        placeholder="••••••••"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        required
                     />

                     {error && (
                        <p className="text-red-400 text-sm text-center">{error}</p>
                     )}

                     <Button
                        type="submit"
                        className="w-full"
                        size="lg"
                        loading={loading}
                     >
                        {isLogin ? "Sign In" : "Create Account"}
                     </Button>
                  </form>

                  <div className="mt-6 text-center">
                     <button
                        type="button"
                        onClick={() => setIsLogin(!isLogin)}
                        className="text-white/60 hover:text-white transition-colors text-sm"
                     >
                        {isLogin
                           ? "Don't have an account? Sign up"
                           : "Already have an account? Sign in"}
                     </button>
                  </div>
               </div>
            </div>
         </div>
      </div>
   );
}

