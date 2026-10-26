/**
 * Backend API Client for LEXIAI
 * Anchors all calls to NEXT_PUBLIC_API_BASE_URL with fallback to http://localhost:8000.
 * Automatically injects stored JWT Bearer token into Authorization headers.
 */

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export function getAuthToken(): string {
  if (typeof window === "undefined") return "";
  return localStorage.getItem("token") || "";
}

export async function apiFetch(endpoint: string, options: RequestInit = {}): Promise<Response> {
  const token = getAuthToken();
  const headers = new Headers(options.headers || {});

  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const cleanEndpoint = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
  const url = `${API_BASE_URL}${cleanEndpoint}`;

  // Retry up to 2 times for transient network/connection drops (e.g. uvicorn reload)
  const maxAttempts = 3;
  let lastError: any = null;

  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    try {
      const response = await fetch(url, { ...options, headers });
      
      // If 401 Unauthorized, the token has expired or is invalid
      if (response.status === 401 && token) {
        if (typeof window !== "undefined") {
          localStorage.removeItem("token");
          window.dispatchEvent(new CustomEvent("lexiai:auth-expired"));
        }
      }

      return response;
    } catch (err: any) {
      lastError = err;
      // Only retry on network errors (e.g. Failed to fetch) and for safe methods
      const method = (options.method || "GET").toUpperCase();
      if ((method === "GET" || method === "HEAD") && attempt < maxAttempts) {
        await new Promise((resolve) => setTimeout(resolve, attempt * 600));
        continue;
      }
      throw new Error(
        `Unable to connect to backend server at ${API_BASE_URL}. Please ensure the backend is running.`
      );
    }
  }

  throw lastError || new Error("Failed to fetch from backend API.");
}

