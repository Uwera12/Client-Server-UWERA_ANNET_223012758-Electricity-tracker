"use client";
import { useCallback, useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { RequireAuth, Loading, Empty, ErrorBox } from "@/components/States";
import UsageChart from "@/components/UsageChart";
import ReadingForm from "@/components/ReadingForm";
import MeterForm from "@/components/MeterForm";

function MeterDetail() {
  const { id } = useParams();
  const router = useRouter();
  const [meter, setMeter] = useState(null);
  const [meterError, setMeterError] = useState(null);
  const [editing, setEditing] = useState(false);
  const [data, setData] = useState(null);          // {count, next, previous, results}
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const [ordering, setOrdering] = useState("-read_date");
  const [version, setVersion] = useState(0);       // bump to refresh table + chart

  useEffect(() => { api(`/meters/${id}/`).then(setMeter).catch(setMeterError); }, [id, version]);

  const loadReadings = useCallback(() => {
    setData(null); setError(null);
    api(`/meters/${id}/readings/?page=${page}&ordering=${ordering}`).then(setData).catch(setError);
  }, [id, page, ordering]);
  useEffect(loadReadings, [loadReadings, version]);

  const refresh = () => setVersion((v) => v + 1);
  const sortBy = (field) => { setPage(1); setOrdering(ordering === field ? `-${field}` : field); };
  const arrow = (field) => (ordering === field ? " ▲" : ordering === `-${field}` ? " ▼" : "");

  async function removeReading(r) {
    if (!confirm(`Delete the reading of ${r.kwh} kWh on ${r.read_date}?`)) return;
    try { await api(`/readings/${r.id}/`, { method: "DELETE" }); if (data.results.length === 1 && page > 1) setPage(page - 1); refresh(); }
    catch (e) { alert(e.message); }
  }
  async function removeMeter() {
    if (!confirm("Delete this meter and ALL its readings?")) return;
    try { await api(`/meters/${id}/`, { method: "DELETE" }); router.push("/meters"); } catch (e) { alert(e.message); }
  }

  if (meterError) return <ErrorBox error={meterError} />;
  if (!meter) return <Loading />;

  return (
    <section>
      <p><Link href="/meters">← All meters</Link></p>
      <div className="row">
        <div>
          <h1>{meter.name}</h1>
          <p className="mut">No. {meter.meter_number}{meter.location ? ` · ${meter.location}` : ""}</p>
        </div>
        <div className="actions">
          <button className="btn ghost" onClick={() => setEditing(!editing)}>{editing ? "Cancel" : "Edit"}</button>
          <button className="btn danger" onClick={removeMeter}>Delete meter</button>
        </div>
      </div>
      {editing && <div className="card"><MeterForm initial={meter} submitLabel="Save changes" onSaved={() => { setEditing(false); refresh(); }} /></div>}

      <h2>Usage and bill estimate</h2>
      <UsageChart meterId={id} refreshKey={version} />

      <h2>Add a reading</h2>
      <div className="card"><ReadingForm meterId={id} onSaved={() => { setPage(1); refresh(); }} /></div>

      <h2>Readings</h2>
      {error ? <ErrorBox error={error} onRetry={loadReadings} /> : !data ? <Loading text="Loading readings…" /> : data.count === 0 ? (
        <Empty>No readings yet. Enter what your meter shows in the form above.</Empty>
      ) : (
        <>
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th><button className="link" onClick={() => sortBy("read_date")}>Date{arrow("read_date")}</button></th>
                  <th><button className="link" onClick={() => sortBy("kwh")}>Reading (kWh){arrow("kwh")}</button></th>
                  <th>Used since previous</th><th></th>
                </tr>
              </thead>
              <tbody>
                {data.results.map((r) => (
                  <tr key={r.id}>
                    <td>{r.read_date}</td><td>{r.kwh}</td>
                    <td>{r.consumption_kwh == null ? "— (first reading)" : `${r.consumption_kwh} kWh`}</td>
                    <td><button className="btn small danger" onClick={() => removeReading(r)}>Delete</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="pager">
            <button className="btn small" disabled={!data.previous} onClick={() => setPage(page - 1)}>← Previous</button>
            <span>Page {page} · {data.count} readings</span>
            <button className="btn small" disabled={!data.next} onClick={() => setPage(page + 1)}>Next →</button>
          </div>
        </>
      )}
    </section>
  );
}

export default function Page() { return <RequireAuth><MeterDetail /></RequireAuth>; }
