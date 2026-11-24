"use client";
import { useEffect, useState } from "react";
import { api, money } from "@/lib/api";
import { RequireAuth, Loading, ErrorBox } from "@/components/States";

function Estimator() {
  const [kwh, setKwh] = useState(100);
  const [bill, setBill] = useState(null);
  const [tariffs, setTariffs] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api("/tariffs/").then(setTariffs).catch(setError);
  }, []);
  useEffect(() => {
    if (kwh === "" || Number(kwh) < 0) return;
    let cancelled = false;
    const t = setTimeout(
      () =>
        api(`/bill/estimate/?kwh=${kwh}`)
          .then((b) => !cancelled && (setBill(b), setError(null)))
          .catch((e) => !cancelled && setError(e)),
      250,
    );
    return () => {
      cancelled = true;
      clearTimeout(t);
    };
  }, [kwh]);

  return (
    <section>
      <h1>Bill estimator</h1>
      <p className="mut">
        Type a monthly usage to see what it would cost. The server applies the
        tariff bands.
      </p>
      <label className="pick">
        Monthly usage (kWh){" "}
        <input
          type="number"
          min="0"
          value={kwh}
          onChange={(e) => setKwh(e.target.value)}
        />
      </label>
      <input
        type="range"
        min="0"
        max="500"
        value={kwh || 0}
        onChange={(e) => setKwh(e.target.value)}
        className="range"
        aria-label="kWh slider"
      />
      {error && <ErrorBox error={error} />}
      {bill && (
        <div className="card">
          <p className="big">{money(bill.total_rwf)}</p>
          <table className="mini">
            <thead>
              <tr>
                <th>Band</th>
                <th>kWh in band</th>
                <th>Rate (RWF/kWh)</th>
                <th>Charge</th>
              </tr>
            </thead>
            <tbody>
              {bill.lines.map((l) => (
                <tr key={l.band}>
                  <td>{l.band}</td>
                  <td>{l.kwh}</td>
                  <td>{l.rate_rwf}</td>
                  <td>{money(l.charge_rwf)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <h2>Tariff bands</h2>
      {!tariffs ? (
        <Loading />
      ) : (
        <table className="mini">
          <thead>
            <tr>
              <th>Band</th>
              <th>From kWh</th>
              <th>To kWh</th>
              <th>Rate (RWF/kWh)</th>
            </tr>
          </thead>
          <tbody>
            {tariffs.map((t) => (
              <tr key={t.id}>
                <td>{t.name}</td>
                <td>{t.from_kwh}</td>
                <td>{t.to_kwh ?? "no limit"}</td>
                <td>{t.rate_rwf}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}

export default function Page() {
  return (
    <RequireAuth>
      <Estimator />
    </RequireAuth>
  );
}
