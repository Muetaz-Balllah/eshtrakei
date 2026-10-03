"use client";

import { FormEvent, useEffect, useState } from "react";
import { RoleShell } from "@/components/shell/role-shell";
import { cardClass, dangerButton, fieldClass, Notice, primaryButton } from "@/components/ui/ui";
import { apiFetch, apiUrl, authHeaders } from "@/lib/api";
import { ar } from "@/messages/ar";

type Banner = {
  id: number;
  title: string;
  body: string;
  image_url: string | null;
  status: string;
  price: string;
  company_id: number | null;
  company_name: string;
  company_balance: string | null;
};
type Ledger = { id: number; company_name: string; amount: string; note: string; kind: string };

export default function BannersPage() {
  const [rows, setRows] = useState<Banner[]>([]);
  const [ledger, setLedger] = useState<Ledger[]>([]);
  const [notice, setNotice] = useState("");

  async function reload() {
    const headers = authHeaders();
    const [banners, entries] = await Promise.all([
      apiFetch("/api/admin/banners", { headers }),
      apiFetch("/api/admin/ledger", { headers }),
    ]);
    if (banners.ok) setRows(await banners.json());
    if (entries.ok) setLedger(await entries.json());
  }

  useEffect(() => {
    reload();
  }, []);

  async function review(id: number, action: "approve" | "reject") {
    const response = await apiFetch(`/api/admin/banners/${id}/${action}`, { method: "POST", headers: authHeaders() });
    const body = await response.json().catch(() => ({}));
    setNotice(body.message ?? (response.ok ? ar.save : ar.purchaseFail));
    await reload();
  }

  async function credit(event: FormEvent<HTMLFormElement>, companyId: number) {
    event.preventDefault();
    const form = event.currentTarget;
    const response = await apiFetch(`/api/admin/companies/${companyId}/credits`, {
      method: "POST",
      headers: { ...authHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({ amount: new FormData(form).get("amount"), note: ar.creditBalance }),
    });
    const body = await response.json().catch(() => ({}));
    setNotice(body.message ?? ar.purchaseFail);
    if (response.ok) {
      form.reset();
      await reload();
    }
  }

  const label = (status: string) => (status === "approved" ? ar.bannerApproved : status === "rejected" ? ar.bannerRejected : ar.bannerPending);

  return (
    <RoleShell role="platform_admin" title={ar.banners}>
      {notice ? <Notice>{notice}</Notice> : null}
      <div className="grid gap-4 lg:grid-cols-2">
        {rows.map((row) => (
          <article key={row.id} className={cardClass}>
            {row.image_url ? <img src={apiUrl(row.image_url)} alt="" className="mb-3 h-36 w-full rounded-2xl object-cover" /> : null}
            <div className="flex items-start justify-between gap-3">
              <div>
                <h2 className="font-extrabold">{row.title}</h2>
                <p className="text-sm text-secondary">{row.company_name}</p>
              </div>
              <span className="rounded-full bg-surface-low px-2.5 py-1 text-xs font-bold">{label(row.status)}</span>
            </div>
            <p className="mt-2 text-sm text-secondary">{row.body}</p>
            <p className="mt-2 text-sm font-bold">{ar.bannerCost}: {row.price} {ar.currency}</p>
            {row.company_balance !== null ? <p className="text-sm text-secondary">{ar.companyBalance}: {row.company_balance} {ar.currency}</p> : null}
            {row.status === "pending_approval" ? (
              <div className="mt-3 flex flex-col gap-2">
                <div className="flex gap-2">
                  <button type="button" className={`${primaryButton} transition hover:opacity-90`} onClick={() => review(row.id, "approve")}>{ar.approveBanner}</button>
                  <button type="button" className={`${dangerButton} transition hover:opacity-90`} onClick={() => review(row.id, "reject")}>{ar.rejectBanner}</button>
                </div>
                {row.company_id ? (
                  <form className="flex gap-2" onSubmit={(event) => credit(event, row.company_id!)}>
                    <input name="amount" required type="number" min="0.01" step="0.01" placeholder={ar.creditBalance} className={fieldClass} />
                    <button className={`${primaryButton} shrink-0 transition hover:opacity-90`} type="submit">{ar.creditBalance}</button>
                  </form>
                ) : null}
              </div>
            ) : null}
          </article>
        ))}
      </div>
      {ledger.length > 0 ? (
        <section className={`${cardClass} flex flex-col gap-2`}>
          <h2 className="font-extrabold">{ar.ledger}</h2>
          {ledger.slice(0, 8).map((row) => (
            <p key={row.id} className="flex items-center justify-between rounded-2xl bg-surface-low px-3 py-2 text-sm">
              <span>{row.company_name} — {row.note}</span>
              <span className="font-bold" dir="ltr">{row.amount}</span>
            </p>
          ))}
        </section>
      ) : null}
    </RoleShell>
  );
}
