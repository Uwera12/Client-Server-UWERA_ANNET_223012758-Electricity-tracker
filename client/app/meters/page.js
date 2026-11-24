"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { RequireAuth, Loading, Empty, ErrorBox } from "@/components/States";

function MeterList() {
  const [meters, setMeters] = useState(null);
  const [error, setError] = useState(null);
  const load = () => { setMeters(null); setError(null); api("/meters/").then((d) => setMeters(d.results)).catch(setError); };
  useEffect(load, []);

  return (
    <section>
      <div className="row"><h1>My meters</h1><Link className="btn" href="/meters/new">+ Add meter</Link></div>
      {error ? <ErrorBox error={error} onRetry={load} /> : !meters ? <Loading /> : meters.length === 0 ? (
        <Empty>No meters yet. Click “Add meter” to create one.</Empty>
      ) : (
        <div className="cards">
          {meters.map((m) => (
            <Link key={m.id} href={`/meters/${m.id}`} className="card meter">
              <h2>{m.name}</h2>
              <p className="mut">No. {m.meter_number}{m.location ? ` · ${m.location}` : ""}</p>
              <p className="big">{m.latest_kwh != null ? `${m.latest_kwh} kWh` : "No readings yet"}</p>
              {m.latest_read_date && <small>last reading on {m.latest_read_date}</small>}
            </Link>
          ))}
        </div>
      )}
    </section>
  );
}

export default function Page() { return <RequireAuth><MeterList /></RequireAuth>; }
