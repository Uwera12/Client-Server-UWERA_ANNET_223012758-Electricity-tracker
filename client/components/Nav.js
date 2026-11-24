"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "./AuthProvider";
import { MENUS } from "@/lib/roles";

export default function Nav() {
  const { session, me, signOut } = useAuth();
  const pathname = usePathname();
  const items = me ? MENUS[me.role] || [] : [];
  return (
    <header className="nav">
      <Link href="/" className="brand">⚡ Electricity Usage Tracker</Link>
      <nav>
        {items.map((i) => (
          <Link key={i.href} href={i.href} className={pathname === i.href ? "active" : ""}>{i.label}</Link>
        ))}
      </nav>
      <div className="who">
        {session ? (
          <>
            <span>{me?.email} <em>({me?.role || "…"})</em></span>
            <button className="btn small" onClick={signOut}>Log out</button>
          </>
        ) : (
          <Link href="/login">Log in</Link>
        )}
      </div>
    </header>
  );
}
