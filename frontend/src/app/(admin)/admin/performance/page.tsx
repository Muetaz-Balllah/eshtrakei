"use client";

import { useEffect, useState } from "react";
import { RoleShell } from "@/components/shell/role-shell";
import { cardClass, Icon } from "@/components/ui/ui";
import { apiFetch, authHeaders } from "@/lib/api";
import { ar } from "@/messages/ar";

type Performance = {
  total_gross_sales: string;
  total_platform_net_revenue: string;
  total_active_companies: number;
  total_registered_clients: number;
  total_active_subscriptions: number;
};

export default function PerformancePage() {
  const [data, setData] = useState<Performance | null>(null);

  useEffect(() => {
    apiFetch("/api/admin/performance", { headers: authHeaders() })
      .then((response) => (response.ok ? response.json() : null))
      .then(setData);
  }, []);

  const tiles = data
    ? [
        { label: ar.grossSales, value: `${data.total_gross_sales} ${ar.currency}`, icon: "payments", featured: true },
        { label: ar.platformRevenue, value: `${data.total_platform_net_revenue} ${ar.currency}`, icon: "account_balance_wallet", featured: true },
        { label: ar.activeCompanies, value: String(data.total_active_companies), icon: "apartment", featured: false },
        { label: ar.registeredClients, value: String(data.total_registered_clients), icon: "group", featured: false },
        { label: ar.activeSubscriptions, value: String(data.total_active_subscriptions), icon: "wifi", featured: false },
      ]
    : [];

  return (
    <RoleShell role="platform_admin" title={ar.performance}>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {tiles.map((tile) => (
          <article
            key={tile.label}
            className={
              tile.featured
                ? "relative overflow-hidden rounded-3xl bg-[#213145] p-5 text-[#eaf1ff] shadow-[0_12px_28px_rgba(0,0,0,0.28)] sm:col-span-2 xl:col-span-1"
                : `${cardClass} flex flex-col gap-3`
            }
          >
            <div className="flex items-center justify-between">
              <p className={tile.featured ? "text-sm text-[#d5e3ff]" : "text-sm font-semibold text-secondary"}>{tile.label}</p>
              <span className={`flex h-10 w-10 items-center justify-center rounded-2xl ${tile.featured ? "bg-primary-container text-white" : "bg-surface-container text-secondary"}`}>
                <Icon name={tile.icon} className="text-[20px]" />
              </span>
            </div>
            <p className="text-3xl font-extrabold">{tile.value}</p>
          </article>
        ))}
      </div>
    </RoleShell>
  );
}
