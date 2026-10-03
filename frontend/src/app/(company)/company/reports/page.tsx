"use client";

import { useEffect, useState } from "react";
import { RoleShell } from "@/components/shell/role-shell";
import { cardClass, Icon } from "@/components/ui/ui";
import { apiFetch, authHeaders } from "@/lib/api";
import { ar } from "@/messages/ar";

type Sale = { created_at: string; client_name: string; package_name: string; amount: string; currency: string };
type Report = { sales_total: string; profit_total: string; currency: string; commission_percentage: number; sales: Sale[] };

export default function ReportsPage() {
  const [report, setReport] = useState<Report | null>(null);

  useEffect(() => {
    apiFetch("/api/company/reports/sales", { headers: authHeaders() })
      .then((response) => (response.ok ? response.json() : null))
      .then(setReport);
  }, []);

  return (
    <RoleShell role="company_manager" title={ar.sales}>
      {report ? (
        <>
          <div className="grid gap-4 lg:grid-cols-2">
            <article className="relative overflow-hidden rounded-3xl bg-[#213145] p-6 text-[#eaf1ff] shadow-[0_12px_28px_rgba(0,0,0,0.28)]">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-sm text-[#d5e3ff]">{ar.salesTotal}</p>
                  <p className="mt-1 text-4xl font-extrabold">{report.sales_total} <span className="text-xl text-primary-fixed">{ar.currency}</span></p>
                </div>
                <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary-container text-white">
                  <Icon name="account_balance_wallet" />
                </span>
              </div>
            </article>
            <article className={`${cardClass} flex flex-col justify-between`}>
              <p className="text-sm font-semibold text-secondary">{ar.profitTotal} ({report.commission_percentage}%)</p>
              <p className="mt-2 text-3xl font-extrabold text-primary-container">{report.profit_total} {ar.currency}</p>
            </article>
          </div>
          <div className="overflow-x-auto rounded-3xl bg-surface-lowest shadow-[0_10px_25px_-5px_rgba(30,58,95,0.07)]">
            <table className="w-full min-w-[36rem] text-sm">
              <thead className="bg-surface-low text-secondary">
                <tr>
                  <th className="px-4 py-3 text-start font-bold">{ar.clients}</th>
                  <th className="px-4 py-3 text-start font-bold">{ar.packages}</th>
                  <th className="px-4 py-3 text-start font-bold">{ar.price}</th>
                </tr>
              </thead>
              <tbody>
                {report.sales.map((sale) => (
                  <tr key={`${sale.created_at}-${sale.client_name}`} className="border-t border-outline-variant/40">
                    <td className="px-4 py-3 font-semibold">{sale.client_name}</td>
                    <td className="px-4 py-3">{sale.package_name}</td>
                    <td className="px-4 py-3 font-bold">{sale.amount} {ar.currency}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      ) : null}
    </RoleShell>
  );
}
