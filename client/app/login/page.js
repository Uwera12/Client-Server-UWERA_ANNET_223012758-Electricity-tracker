"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { supabase, supabaseConfigured } from "@/lib/supabaseClient";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState("login");
  const [form, setForm] = useState({ full_name: "", email: "", password: "" });
  const [msg, setMsg] = useState(null);
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  async function submit(e) {
    e.preventDefault();
    setBusy(true); setMsg(null);
    if (mode === "signup") {
      const { data, error } = await supabase.auth.signUp({
        email: form.email, password: form.password, options: { data: { full_name: form.full_name } },
      });
      if (error) setMsg({ type: "error", text: error.message });
      else if (!data.session) setMsg({ type: "ok", text: "Account created. Check your email to confirm it, then log in." });
      else router.push("/");
    } else {
      const { error } = await supabase.auth.signInWithPassword({ email: form.email, password: form.password });
      if (error) setMsg({ type: "error", text: error.message });
      else router.push("/");
    }
    setBusy(false);
  }

  return (
    <section className="card narrow">
      <h1>{mode === "login" ? "Log in" : "Create your household account"}</h1>
      {!supabaseConfigured && <p className="msg error">Supabase keys are missing. Create client/.env.local first.</p>}
      <form onSubmit={submit} className="form">
        {mode === "signup" && <label>Full name<input value={form.full_name} onChange={set("full_name")} required /></label>}
        <label>Email<input type="email" value={form.email} onChange={set("email")} required /></label>
        <label>Password<input type="password" minLength={6} value={form.password} onChange={set("password")} required /></label>
        {msg && <p className={`msg ${msg.type}`} role="alert">{msg.text}</p>}
        <button className="btn" disabled={busy}>{busy ? "Please wait…" : mode === "login" ? "Log in" : "Sign up"}</button>
      </form>
      <p>
        {mode === "login" ? "New here? " : "Already have an account? "}
        <button className="link" onClick={() => { setMode(mode === "login" ? "signup" : "login"); setMsg(null); }}>
          {mode === "login" ? "Create an account" : "Log in"}
        </button>
      </p>
    </section>
  );
}
