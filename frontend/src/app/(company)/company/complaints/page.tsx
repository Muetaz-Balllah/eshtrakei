"use client";

import { FormEvent, useEffect, useState } from "react";
import { RoleShell } from "@/components/shell/role-shell";
import { cardClass, fieldClass, ghostButton } from "@/components/ui/ui";
import { apiFetch, authHeaders } from "@/lib/api";
import { ar } from "@/messages/ar";

type Complaint = { id: number; message: string; reply_message: string | null };

export default function CompanyComplaintsPage() {
  const [rows, setRows] = useState<Complaint[]>([]);

  async function reload() {
    const response = await apiFetch("/api/company/complaints", { headers: authHeaders() });
    if (response.ok) setRows(await response.json());
  }

  useEffect(() => {
    reload();
  }, []);

  async function reply(event: FormEvent<HTMLFormElement>, id: number) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    await apiFetch(`/api/company/complaints/${id}/reply`, {
      method: "POST",
      headers: { ...authHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({ message: form.get("message") }),
    });
    await reload();
  }

  return (
    <RoleShell role="company_manager" title={ar.complaints}>
      <div className="grid gap-4 lg:grid-cols-2">
        {rows.map((row) => (
          <article key={row.id} className={`${cardClass} flex flex-col gap-3`}>
            <p className="font-semibold">{row.message}</p>
            <p className="rounded-2xl bg-surface-low px-3 py-2 text-sm text-secondary">{row.reply_message ?? ar.noReply}</p>
            <form className="flex flex-col gap-2" onSubmit={(event) => reply(event, row.id)}>
              <textarea name="message" required rows={3} placeholder={ar.reply} className={fieldClass} />
              <button className={`${ghostButton} w-fit`} type="submit">{ar.sendReply}</button>
            </form>
          </article>
        ))}
      </div>
    </RoleShell>
  );
}
