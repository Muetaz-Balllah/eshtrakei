"use client";

import { useEffect, useState } from "react";
import { RoleShell } from "@/components/shell/role-shell";
import { Badge, cardClass, Icon, navyButton, Notice } from "@/components/ui/ui";
import { apiFetch, authHeaders } from "@/lib/api";
import { ar } from "@/messages/ar";

type Sub = {
  id: number;
  company_name: string;
  package_name: string;
  status: string;
  start_date: string;
  end_date: string;
  days_remaining: number;
  price: string;
};

const labels: Record<string, string> = { active: ar.active, upcoming: ar.upcoming, expired: ar.expired };
const tones: Record<string, "ok" | "warn" | "bad" | "neutral"> = { active: "ok", upcoming: "warn", expired: "bad" };

export default function SubscriptionsPage() {
  const [rows, setRows] = useState<Sub[]>([]);
  const [notice, setNotice] = useState("");

  async function reload() {
    const response = await apiFetch("/api/subscriptions", { headers: authHeaders() });
    if (response.ok) setRows(await response.json());
  }

  useEffect(() => {
    reload();
  }, []);

  async function renew(id: number) {
    const response = await apiFetch(`/api/subscriptions/${id}/renew`, {
      method: "POST",
      headers: { ...authHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({ idempotency_key: crypto.randomUUID(), simulated_outcome: "success" }),
    });
    const body = await response.json();
    setNotice(response.ok && body.payment_status === "succeeded" ? `${ar.purchaseOk} — ${ar.invoiceNo} ${body.invoice.invoice_number}` : body.message);
    await reload();
  }

  return (
    <RoleShell role="client" title={ar.subscriptions}>
      {notice ? <Notice>{notice}</Notice> : null}
      <div className="grid gap-4 lg:grid-cols-2">
        {rows.map((row) => (
          <article key={row.id} className={`${cardClass} flex flex-col gap-4`}>
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-sm font-semibold text-secondary">{row.company_name}</p>
                <h2 className="text-xl font-extrabold">{row.package_name}</h2>
              </div>
              <Badge tone={tones[row.status] ?? "neutral"}>{labels[row.status] ?? row.status}</Badge>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-2xl bg-surface-low p-4 text-center">
                <Icon name="timer" className="text-secondary" />
                <p className="mt-1 text-xs text-secondary">{ar.daysLeft}</p>
                <p className="text-lg font-extrabold">{row.days_remaining}</p>
              </div>
              <div className="rounded-2xl bg-primary-container p-4 text-center text-white">
                <Icon name="payments" />
                <p className="mt-1 text-xs text-white/80">{ar.price}</p>
                <p className="text-lg font-extrabold">{row.price} {ar.currency}</p>
              </div>
            </div>
            <p className="text-center text-xs font-semibold text-secondary" dir="ltr">{row.start_date} — {row.end_date}</p>
            <button type="button" className={navyButton} onClick={() => renew(row.id)}>
              <Icon name="refresh" className="text-[20px]" />
              {ar.renew}
            </button>
          </article>
        ))}
      </div>
    </RoleShell>
  );
}
