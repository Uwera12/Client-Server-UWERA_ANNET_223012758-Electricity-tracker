"use client";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuth } from "./AuthProvider";
import { supabaseConfigured } from "@/lib/supabaseClient";

export const Loading = ({ text = "Loading…" }) => <p className="state loading" role="status">⏳ {text}</p>;
export const Empty = ({ children }) => <p className="state empty">{children}</p>;
export const ErrorBox = ({ error, onRetry }) => (
  <div className="state error" role="alert">
    <strong>Something went wrong.</strong> {error?.message || String(error)}
    {error?.status ? <small> (HTTP {error.status})</small> : null}
    {onRetry && <button className="btn small" onClick={onRetry}>Try again</button>}
  </div>
);

/** Wrap every protected page: sends visitors to /login and blocks roles that are not allowed. */
export function RequireAuth({ children }) {
  const { session, me, loading } = useAuth();
  const router = useRouter();
  useEffect(() => { if (!loading && !session) router.replace("/login"); }, [loading, session, router]);

  if (!supabaseConfigured)
    return <ErrorBox error={{ message: "Supabase keys are missing. Create client/.env.local (see .env.local.example) and restart." }} />;
  if (loading || !session) return <Loading text="Checking your login…" />;
  if (!me) return <ErrorBox error={{ message: "The server could not confirm who you are. Check that Django is running, then log in again." }} />;
  if (me.role !== "household") return <ErrorBox error={{ message: "Your role cannot use this app.", status: 403 }} />;
  return children;
}
