"use client";
import { createContext, useContext, useEffect, useState } from "react";
import { supabase } from "@/lib/supabaseClient";
import { api } from "@/lib/api";

const Ctx = createContext({ session: null, me: null, loading: true, signOut: () => {} });
export const useAuth = () => useContext(Ctx);

export default function AuthProvider({ children }) {
  const [session, setSession] = useState(null);
  const [me, setMe] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      setSession(data.session);
      if (!data.session) setLoading(false);
    });
    const { data: sub } = supabase.auth.onAuthStateChange((_event, s) => {
      setSession(s);
      if (!s) { setMe(null); setLoading(false); }
    });
    return () => sub.subscription.unsubscribe();
  }, []);

  // Ask Django who this user is and what role they have.
  useEffect(() => {
    if (!session) return;
    let cancelled = false;
    api("/me/")
      .then((m) => !cancelled && setMe(m))
      .catch(() => !cancelled && setMe(null))
      .finally(() => !cancelled && setLoading(false));
    return () => { cancelled = true; };
  }, [session?.access_token]);

  const signOut = () => supabase.auth.signOut();
  return <Ctx.Provider value={{ session, me, loading, signOut }}>{children}</Ctx.Provider>;
}
