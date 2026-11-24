import { createClient } from "@supabase/supabase-js";

const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

export const supabaseConfigured = Boolean(url && key);

// The client only ever uses Supabase for LOGIN. All data goes through Django.
export const supabase = createClient(url || "http://localhost:54321", key || "missing-key");
