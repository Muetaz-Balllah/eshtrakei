"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { InlineAccount } from "@/components/account/inline-account";
import { RoleShell, useLogout } from "@/components/shell/role-shell";
import { ThemeToggle } from "@/components/shell/theme-toggle";
import { Icon } from "@/components/ui/ui";
import { apiFetch, apiUrl, authHeaders } from "@/lib/api";
import { readCompanyId, writeCompanyId } from "@/lib/selected-company";
import { ar } from "@/messages/ar";

type Me = { full_name: string; phone: string | null; email: string; city: string | null; avatar_url: string | null };
type Company = { id: number; name: string };

const rowClass = "flex w-full items-center justify-between rounded-2xl p-3 text-start transition hover:bg-surface-low";

export default function ClientSettingsPage() {
  const logout = useLogout();
  const [me, setMe] = useState<Me | null>(null);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [selected, setSelected] = useState<number | null>(null);

  useEffect(() => {
    const headers = authHeaders();
    apiFetch("/api/auth/me", { headers }).then(async (response) => {
      if (response.ok) setMe(await response.json());
    });
    fetch(apiUrl("/api/companies"), { headers }).then(async (response) => {
      const rows: Company[] = response.ok ? await response.json() : [];
      setCompanies(rows);
      const saved = readCompanyId();
      setSelected(rows.find((row) => row.id === saved)?.id ?? rows[0]?.id ?? null);
    });
  }, []);

  function choose(id: number) {
    setSelected(id);
    writeCompanyId(id);
  }

  const company = companies.find((row) => row.id === selected);
  const photo = me?.avatar_url ? apiUrl(me.avatar_url) : "";

  return (
    <RoleShell role="client" title={ar.settings}>
      <section className="flex flex-col gap-4 rounded-3xl bg-surface-lowest p-5 shadow-[0_10px_25px_-5px_rgba(30,58,95,0.07)]">
        <div className="flex items-center justify-between gap-3">
          <div className="flex min-w-0 items-center gap-3">
            <span className="relative flex h-16 w-16 shrink-0 items-center justify-center overflow-hidden rounded-full bg-surface-container text-secondary">
              {photo ? <img src={photo} alt="" className="h-full w-full object-cover" /> : <Icon name="person" className="text-[32px]" />}
            </span>
            <div className="min-w-0">
              <p className="truncate font-extrabold">{me?.full_name}</p>
              <p dir="ltr" className="truncate text-sm text-secondary">{me?.phone || me?.email}</p>
            </div>
          </div>
        </div>
        <Link href="/client/wallet" className="inline-flex w-fit items-center gap-1.5 rounded-2xl bg-primary-container px-4 py-2.5 text-sm font-bold text-white transition hover:opacity-90">
          <Icon name="account_balance_wallet" className="text-[18px]" />
          {ar.topUp}
        </Link>
      </section>

      <section className="flex flex-col gap-2">
        <h3 className="px-2 font-bold text-secondary">{ar.securityAccess}</h3>
        <div className="flex flex-col rounded-3xl bg-surface-lowest p-2 shadow-[0_10px_25px_-5px_rgba(30,58,95,0.07)]">
          <InlineAccount />
        </div>
      </section>

      <section className="flex items-center justify-between rounded-3xl bg-surface-lowest p-4 shadow-[0_10px_25px_-5px_rgba(30,58,95,0.07)]">
        <span className="flex items-center gap-3 font-bold">
          <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-surface-container text-secondary"><Icon name="dark_mode" className="text-[22px]" /></span>
          {ar.darkMode}
        </span>
        <ThemeToggle />
      </section>

      <section className="flex flex-col gap-3 rounded-3xl bg-surface-lowest p-4 shadow-[0_10px_25px_-5px_rgba(30,58,95,0.07)]">
        <div className="flex gap-2 overflow-x-auto">
          {companies.map((row) => (
            <button key={row.id} type="button" onClick={() => choose(row.id)} className={`shrink-0 rounded-full px-3 py-1.5 text-xs font-bold transition hover:opacity-90 ${row.id === company?.id ? "bg-inverse-surface text-inverse-on-surface" : "bg-surface-low text-secondary"}`}>
              {row.name}
            </button>
          ))}
        </div>
        <Link href={company ? `/client/coverage?company=${company.id}` : "/client/coverage"} className={rowClass}>
          <span className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-surface-container text-secondary"><Icon name="map" className="text-[22px]" /></span>
            <span><span className="block font-bold">{ar.coverage}</span><span className="text-sm text-secondary">{company?.name}</span></span>
          </span>
          <Icon name="chevron_left" className="text-secondary" />
        </Link>
      </section>

      <div className="flex flex-col rounded-3xl bg-surface-lowest p-2 shadow-[0_10px_25px_-5px_rgba(30,58,95,0.07)]">
        <Link href="/client/complaints" className={rowClass}><span className="font-bold">{ar.complaints}</span><Icon name="chevron_left" className="text-secondary" /></Link>
        <Link href="/client/invoices" className={rowClass}><span className="font-bold">{ar.invoices}</span><Icon name="chevron_left" className="text-secondary" /></Link>
      </div>

      <button type="button" onClick={logout} className="flex h-12 w-full items-center justify-center gap-2 rounded-2xl bg-error-container font-bold text-error transition hover:opacity-90">
        <Icon name="logout" className="text-[20px]" />
        {ar.logout}
      </button>
    </RoleShell>
  );
}
