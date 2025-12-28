const API_BASE = "/api";

interface ApiResponse<T> {
   data?: T;
   error?: string;
}

async function fetchApi<T>(
   endpoint: string,
   options: RequestInit = {}
): Promise<ApiResponse<T>> {
   const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;

   const headers: HeadersInit = {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
   };

   try {
      const response = await fetch(`${API_BASE}${endpoint}`, {
         ...options,
         headers,
      });

      if (!response.ok) {
         const error = await response.json().catch(() => ({ detail: "Request failed" }));
         return { error: error.detail || "Request failed" };
      }

      const data = await response.json();
      return { data };
   } catch (error) {
      return { error: "Network error" };
   }
}

// Auth
export async function register(email: string, password: string) {
   return fetchApi<{ id: string; email: string }>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password }),
   });
}

export async function login(email: string, password: string) {
   const formData = new URLSearchParams();
   formData.append("username", email);
   formData.append("password", password);

   const response = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: {
         "Content-Type": "application/x-www-form-urlencoded",
      },
      body: formData,
   });

   if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Login failed" }));
      return { error: error.detail || "Login failed" };
   }

   const data = await response.json();
   if (data.access_token) {
      localStorage.setItem("token", data.access_token);
   }
   return { data };
}

export function logout() {
   localStorage.removeItem("token");
}

export async function getMe() {
   return fetchApi<{ id: string; email: string }>("/auth/me");
}

// Apps
export interface App {
   id: string;
   name: string;
   slug: string;
   status: "DRAFT" | "RUNNING" | "STOPPED" | "ERROR" | "DELETING";
   created_at: string;
   updated_at: string;
   owner_user_id: string;
}

export async function listApps() {
   return fetchApi<{ apps: App[]; total: number }>("/apps");
}

export async function generateApp(prompt: string, model?: string) {
   return fetchApi<{ job_id: string; app_id: string }>("/apps/generate", {
      method: "POST",
      body: JSON.stringify({ prompt, model }),
   });
}

export async function getApp(appId: string) {
   return fetchApi<App>(`/apps/${appId}`);
}

export async function startApp(appId: string) {
   return fetchApi<{ status: string }>(`/apps/${appId}/start`, {
      method: "POST",
   });
}

export async function stopApp(appId: string) {
   return fetchApi<{ status: string }>(`/apps/${appId}/stop`, {
      method: "POST",
   });
}

export async function deleteApp(appId: string) {
   return fetchApi<{ status: string }>(`/apps/${appId}`, {
      method: "DELETE",
   });
}

export async function getBlueprint(appId: string) {
   return fetchApi<{
      id: string;
      app_id: string;
      version: number;
      blueprint_json: any;
      validation_status: string;
   }>(`/apps/${appId}/blueprints/latest`);
}

// Jobs
export interface Job {
   id: string;
   app_id: string;
   status: "QUEUED" | "RUNNING" | "SUCCEEDED" | "FAILED";
   model: string;
   prompt: string;
   error_message?: string;
   created_at: string;
   updated_at: string;
}

export async function getJob(jobId: string) {
   return fetchApi<Job>(`/jobs/${jobId}`);
}

// Runtime
export async function getRuntimeApp(slug: string) {
   return fetchApi<{
      status: string;
      app?: { id: string; name: string; slug: string };
      runtime_config?: { db_schema: string; base_path: string };
      blueprint?: any;
      message?: string;
   }>(`/runtime/apps/${slug}`);
}

