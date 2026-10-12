"use client";

import { useEffect, useState } from "react";
import { RoleShell } from "@/components/shell/role-shell";
import { Badge, cardClass, ghostButton, Icon } from "@/components/ui/ui";
import { apiFetch, authHeaders, newIdempotencyKey } from "@/lib/api";
import { ar } from "@/messages/ar";

type Sub = { id: number; package_name: string; status: string; start_date: string; end_date: string; days_remaining: number };
type ClientRow = { client_id: number; full_name: string; email: string; subscriptions: Sub[] };

const labels: Record<string, string> = { active: ar.active, upcoming: ar.upcoming, expired: ar.expired };
const tones: Record<string, "ok" | "warn" | "bad"> = { active: "ok", upcoming: "warn", expired: "bad" };

export default function CompanyClientsPage() {
  const [rows, setRows] = useState<ClientRow[]>([]);

  useEffect(() => {
    apiFetch("/api/company/clients", { headers: authHeaders() })
      .then((response) => response.json())
      .then(setRows);
  }, []);

  async function renew(id: number) {
    await apiFetch(`/api/company/subscriptions/${id}/renew`, {
      method: "POST",
      headers: { ...authHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({ idempotency_key: newIdempotencyKey(), simulated_outcome: "success" }),
    });
    const response = await apiFetch("/api/company/clients", { headers: authHeaders() });
    setRows(await response.json());
  }

  return (
    <RoleShell role="company_manager" title={ar.clients}>
      <div className="grid gap-4 xl:grid-cols-2">
        {rows.map((row) => (
          <article key={row.client_id} className={`${cardClass} flex flex-col gap-3`}>
            <div className="flex items-center gap-3">
              <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-secondary text-on-secondary">
                <Icon name="person" />
              </span>
              <div>
                <h2 className="font-extrabold">{row.full_name}</h2>
                <p dir="ltr" className="text-sm text-secondary">{row.email}</p>
              </div>
            </div>
            {row.subscriptions.map((sub) => (
              <div key={sub.id} className="flex flex-col gap-2 rounded-2xl bg-surface-low p-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <p className="font-bold">{sub.package_name}</p>
                  <p className="text-sm text-secondary">{ar.daysLeft}: {sub.days_remaining}</p>
                  <Badge tone={tones[sub.status] ?? "warn"}>{labels[sub.status] ?? sub.status}</Badge>
                </div>
                <button type="button" className={ghostButton} onClick={() => renew(sub.id)}>{ar.renew}</button>
              </div>
            ))}
          </article>
        ))}
      </div>
    </RoleShell>
  );
}
