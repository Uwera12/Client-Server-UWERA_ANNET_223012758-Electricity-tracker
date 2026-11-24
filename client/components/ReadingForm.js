"use client";
import { useState } from "react";
import { api, today } from "@/lib/api";

/** The server decides if a reading is valid. Whatever it says is shown here as-is. */
export default function ReadingForm({ meterId, onSaved }) {
  const [kwh, setKwh] = useState("");
  const [date, setDate] = useState(today());
  const [error, setError] = useState(null);
  const [ok, setOk] = useState(null);
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setBusy(true); setError(null); setOk(null);
    try {
      const r = await api(`/meters/${meterId}/readings/`, { method: "POST", body: { kwh, read_date: date } });
      setOk(r.consumption_kwh == null ? "First reading saved (this is your starting point)." : `Saved. You used ${r.consumption_kwh} kWh since the last reading.`);
      setKwh("");
      onSaved?.();
    } catch (err) { setError(err); } finally { setBusy(false); }
  }

  return (
    <form onSubmit={submit} className="form inline">
      <label>Meter reading (kWh)<input type="number" step="0.01" min="0" value={kwh} onChange={(e) => setKwh(e.target.value)} placeholder="1500.00" required /></label>
      <label>Date<input type="date" value={date} onChange={(e) => setDate(e.target.value)} required /></label>
      <button className="btn" disabled={busy}>{busy ? "Saving…" : "Submit reading"}</button>
      {error && <p className="msg error" role="alert">{error.message} <small>(HTTP {error.status})</small></p>}
      {ok && <p className="msg ok" role="status">{ok}</p>}
    </form>
  );
}
