"use client";
import { useState } from "react";
import { api } from "@/lib/api";

export default function MeterForm({ initial, onSaved, submitLabel = "Save meter" }) {
  const [form, setForm] = useState({ name: "", meter_number: "", location: "", ...initial });
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  async function submit(e) {
    e.preventDefault();
    setBusy(true); setError(null);
    try {
      const body = { name: form.name, meter_number: form.meter_number, location: form.location || null };
      const saved = initial?.id ? await api(`/meters/${initial.id}/`, { method: "PATCH", body }) : await api("/meters/", { method: "POST", body });
      onSaved(saved);
    } catch (err) { setError(err); } finally { setBusy(false); }
  }

  return (
    <form onSubmit={submit} className="form">
      <label>Name<input value={form.name} onChange={set("name")} maxLength={100} placeholder="Home" required /></label>
      <label>Meter number<input value={form.meter_number} onChange={set("meter_number")} maxLength={50} placeholder="0412-5567-001" required /></label>
      <label>Location (optional)<input value={form.location || ""} onChange={set("location")} maxLength={200} placeholder="Kimironko, Kigali" /></label>
      {error && <p className="msg error" role="alert">{error.message}</p>}
      <button className="btn" disabled={busy}>{busy ? "Saving…" : submitLabel}</button>
    </form>
  );
}
