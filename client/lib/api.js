import { supabase } from "./supabaseClient";

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ??
  (process.env.NODE_ENV === "development" ? "http://localhost:8000" : "");

export class ApiError extends Error {
  constructor(status, message, details) {
    super(message);
    this.status = status;
    this.details = details;
  }
}

/** Calls the Django API, attaching the Supabase access token. Throws ApiError with a readable message. */
export async function api(path, { method = "GET", body } = {}) {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  let res;
  try {
    res = await fetch(`${API_URL}/api${path}`, {
      method,
      headers: {
        ...(body ? { "Content-Type": "application/json" } : {}),
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: body ? JSON.stringify(body) : undefined,
    });
  } catch {
    throw new ApiError(0, `Cannot reach the server at ${API_URL}. Is Django running?`);
  }
  if (res.status === 204) return null;
  const json = await res.json().catch(() => null);
  if (!res.ok) throw new ApiError(res.status, json?.error || `Request failed (${res.status})`, json?.details);
  return json;
}

export const money = (n) => `${Math.round(n).toLocaleString()} RWF`;
export const today = () => new Date().toLocaleDateString("en-CA"); // YYYY-MM-DD in local time
