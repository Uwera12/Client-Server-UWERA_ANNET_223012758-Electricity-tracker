"use client";
import { useCallback, useEffect, useState } from "react";
import { api, money } from "@/lib/api";
import { Empty, ErrorBox, Loading } from "./States";

const MONTHS = [
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "May",
  "Jun",
  "Jul",
  "Aug",
  "Sep",
  "Oct",
  "Nov",
  "Dec",
];
const label = (ym) => `${MONTHS[Number(ym.slice(5)) - 1]} ${ym.slice(2, 4)}`;

/** Bar chart of monthly kWh. Click a bar to see that month's bill estimate. meterId=null means all meters. */
export default function UsageChart({ meterId = null, refreshKey = 0 }) {
  const [months, setMonths] = useState(null);
  const [error, setError] = useState(null);
  const [picked, setPicked] = useState(null);
  const [bill, setBill] = useState(null);

  const load = useCallback(() => {
    setMonths(null);
    setError(null);
    api(`/analytics/monthly/${meterId ? `?meter=${meterId}` : ""}`)
      .then((d) => {
        setMonths(d.months);
        setPicked(d.months.length ? d.months[d.months.length - 1].month : null);
      })
      .catch(setError);
  }, [meterId]);

  useEffect(load, [load, refreshKey]);

  // For a single meter, also fetch the band-by-band breakdown of the chosen month.
  useEffect(() => {
    setBill(null);
    if (!meterId || !picked) return;
    let cancelled = false;
    api(`/meters/${meterId}/bill/?month=${picked}`)
      .then((b) => !cancelled && setBill(b))
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [meterId, picked]);

  if (error) return <ErrorBox error={error} onRetry={load} />;
  if (!months) return <Loading text="Loading usage…" />;
  if (months.length === 0)
    return (
      <Empty>
        No monthly usage yet. Add at least two readings (on different dates) to
        see a chart.
      </Empty>
    );

  const W = 640,
    H = 260,
    pad = { l: 44, r: 12, t: 24, b: 34 };
  const max = Math.max(...months.map((m) => m.kwh), 1);
  const bw = (W - pad.l - pad.r) / months.length;
  const sel = months.find((m) => m.month === picked);

  return (
    <div className="chart-card">
      <div className="chart-scroll">
        <svg
          viewBox={`0 0 ${W} ${H}`}
          role="img"
          aria-label="Monthly electricity consumption in kWh"
        >
          {[0, 0.5, 1].map((f) => {
            const y = pad.t + (H - pad.t - pad.b) * (1 - f);
            return (
              <g key={f}>
                <line x1={pad.l} x2={W - pad.r} y1={y} y2={y} className="grid" />
                <text x={pad.l - 6} y={y + 4} textAnchor="end" className="axis">
                  {Math.round(max * f)}
                </text>
              </g>
            );
          })}
          {months.map((m, i) => {
            const h = ((H - pad.t - pad.b) * m.kwh) / max;
            const barW = Math.min(bw * 0.7, 70);
            const x = pad.l + i * bw + (bw - barW) / 2;
            const y = H - pad.b - h;
            return (
              <g
                key={m.month}
                className={`bar ${m.month === picked ? "on" : ""}`}
                role="button"
                tabIndex={0}
                aria-label={`${label(m.month)}: ${m.kwh} kWh`}
                onClick={() => setPicked(m.month)}
                onKeyDown={(e) =>
                  (e.key === "Enter" || e.key === " ") && setPicked(m.month)
                }
              >
                <rect x={x} y={y} width={barW} height={Math.max(h, 1)} rx="4" />
                <text
                  x={x + barW / 2}
                  y={y - 5}
                  textAnchor="middle"
                  className="val"
                >
                  {m.kwh}
                </text>
                <text
                  x={x + barW / 2}
                  y={H - 12}
                  textAnchor="middle"
                  className="axis"
                >
                  {label(m.month)}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      {sel && (
        <div className="estimate">
          <h3>{label(sel.month)} bill estimate</h3>
          <p className="big">{money(sel.bill_rwf)}</p>
          <p>
            {sel.kwh} kWh used{" "}
            {meterId ? "on this meter" : "across all your meters"}
          </p>
          {bill && (
            <div className="table-scroll">
              <table className="mini">
                <thead>
                  <tr>
                    <th>Band</th>
                    <th>kWh</th>
                    <th>Rate</th>
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
          <small>
            Click another bar to compare months. Rates come from the tariff
            bands in the database.
          </small>
        </div>
      )}
    </div>
  );
}
