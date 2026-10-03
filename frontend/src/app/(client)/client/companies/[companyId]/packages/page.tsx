"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { RoleShell } from "@/components/shell/role-shell";
import { cardClass, ghostButton, Icon, primaryButton } from "@/components/ui/ui";
import { apiFetch, authHeaders } from "@/lib/api";
import { ar } from "@/messages/ar";

type Package = { id: number; name: string; price: string; duration_amount: number; duration_unit: string; data_gb: number; speed_mbps: number };

export default function ClientPackagesPage() {
  const params = useParams<{ companyId: string }>();
  const [rows, setRows] = useState<Package[]>([]);

  useEffect(() => {
    apiFetch(`/api/companies/${params.companyId}/packages`, { headers: authHeaders() })
      .then((response) => (response.ok ? response.json() : []))
      .then(setRows);
  }, [params.companyId]);

  return (
    <RoleShell role="client" title={ar.packages}>
      <Link href="/client/companies" className={`${ghostButton} w-fit`}>
        <Icon name="arrow_forward" className="text-[18px]" />
        {ar.clientHome}
      </Link>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {rows.map((row) => (
          <article key={row.id} className={`${cardClass} flex flex-col gap-4`}>
            <div className="flex items-start justify-between gap-3">
              <h2 className="text-lg font-extrabold">{row.name}</h2>
              <span className="text-2xl font-extrabold text-primary-container">
                {row.price}
                <span className="ms-1 text-sm">{ar.currency}</span>
              </span>
            </div>
            <div className="grid grid-cols-3 gap-2">
              <div className="rounded-2xl bg-surface-low px-2 py-3 text-center">
                <Icon name="schedule" className="text-secondary text-[18px]" />
                <p className="mt-1 text-xs font-bold">{row.duration_amount} {row.duration_unit === "days" ? ar.days : ar.months}</p>
              </div>
              <div className="rounded-2xl bg-surface-low px-2 py-3 text-center">
                <Icon name="database" className="text-secondary text-[18px]" />
                <p className="mt-1 text-xs font-bold" dir="ltr">{row.data_gb} GB</p>
              </div>
              <div className="rounded-2xl bg-surface-low px-2 py-3 text-center">
                <Icon name="speed" className="text-secondary text-[18px]" />
                <p className="mt-1 text-xs font-bold" dir="ltr">{row.speed_mbps} Mbps</p>
              </div>
            </div>
            <Link href={`/client/checkout/${row.id}?company=${params.companyId}`} className={primaryButton}>
              {ar.buy}
            </Link>
          </article>
        ))}
      </div>
    </RoleShell>
  );
}
