"use client";
import { useRouter } from "next/navigation";
import { RequireAuth } from "@/components/States";
import MeterForm from "@/components/MeterForm";

function NewMeter() {
  const router = useRouter();
  return (
    <section className="card narrow">
      <h1>Add a meter</h1>
      <MeterForm submitLabel="Create meter" onSaved={(m) => router.push(`/meters/${m.id}`)} />
    </section>
  );
}

export default function Page() { return <RequireAuth><NewMeter /></RequireAuth>; }
