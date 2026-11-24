"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { RequireAuth, Loading, Empty, ErrorBox } from "@/components/States";
import UsageChart from "@/components/UsageChart";

function Dashboard() {
  const [meters, setMeters] = useState(null);
  const [error, setError] = useState(null);
  const [meterId, setMeterId] = useState("");

  useEffect(() => { api("/meters/").then((d) => setMeters(d.results)).catch(setError); }, []);

  if (error) return <ErrorBox error={error} />;
  if (!meters) return <Loading />;
  if (meters.length === 0)
    return <Empty>You have no meters yet. <Link href="/meters/new">Add your first meter</Link> to start tracking.</Empty>;

  return (
    <section>
      <h1>Your electricity usage</h1>
      <label className="pick">Show usage for{" "}
        <select value={meterId} onChange={(e) => setMeterId(e.target.value)}>
          <option value="">All my meters</option>
          {meters.map((m) => <option key={m.id} value={m.id}>{m.name} ({m.meter_number})</option>)}
        </select>
      </label>
      <UsageChart meterId={meterId || null} />
    </section>
  );
}

export default function Page() { return <RequireAuth><Dashboard /></RequireAuth>; }
