"use client";

import { useEffect, useState } from "react";
import { RoleShell } from "@/components/shell/role-shell";
import { cardClass, ghostButton } from "@/components/ui/ui";
import { apiFetch, authHeaders } from "@/lib/api";
import { ar } from "@/messages/ar";

type Invoice = { id: number; invoice_number: number; amount_paid: string; package_name: string };

export default function InvoicesPage() {
  const [rows, setRows] = useState<Invoice[]>([]);

  useEffect(() => {
    apiFetch("/api/invoices", { headers: authHeaders() }).then(async (response) => {
      if (response.ok) setRows(await response.json());
    });
  }, []);

  async function download(id: number) {
    const response = await apiFetch(`/api/invoices/${id}/pdf`, { headers: authHeaders() });
    if (!response.ok) return;
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `invoice-${id}.pdf`;
    link.click();
    URL.revokeObjectURL(url);
  }

  return (
    <RoleShell role="client" title={ar.invoices}>
      <div className="grid gap-3 lg:grid-cols-2">
        {rows.map((row) => (
          <article key={row.id} className={`${cardClass} flex items-center justify-between gap-3`}>
            <div>
              <p className="font-extrabold">{row.package_name}</p>
              <p className="text-sm text-secondary">{ar.invoiceNo} {row.invoice_number}</p>
              <p className="font-bold">{row.amount_paid} {ar.currency}</p>
            </div>
            <button type="button" className={ghostButton} onClick={() => download(row.id)}>{ar.downloadInvoice}</button>
          </article>
        ))}
      </div>
    </RoleShell>
  );
}
