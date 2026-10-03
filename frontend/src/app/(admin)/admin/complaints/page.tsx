"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { RoleShell } from "@/components/shell/role-shell";
import { cardClass, fieldClass, Icon, Notice } from "@/components/ui/ui";
import { apiFetch, authHeaders } from "@/lib/api";
import { ar } from "@/messages/ar";

type Complaint = {
  id: number;
  kind: string;
  target: string;
  company_name: string | null;
  client_name: string;
  client_phone: string | null;
  message: string;
  created_at: string;
  reply_message: string | null;
  replied_at: string | null;
};

function when(value: string) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("ar-LY", { dateStyle: "medium", timeStyle: "short" });
}

export default function AdminComplaintsPage() {
  const [rows, setRows] = useState<Complaint[]>([]);
  const [query, setQuery] = useState("");
  const [filter, setFilter] = useState<"all" | "open" | "resolved">("all");
  const [notice, setNotice] = useState("");

  async function reload() {
    const response = await apiFetch("/api/admin/complaints", { headers: authHeaders() });
    if (response.ok) setRows(await response.json());
  }

  useEffect(() => {
    reload();
  }, []);

  async function reply(event: FormEvent<HTMLFormElement>, id: number) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const response = await apiFetch(`/api/admin/complaints/${id}/reply`, {
      method: "POST",
      headers: { ...authHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({ message: form.get("message") }),
    });
    if (response.ok) {
      setNotice(ar.sendReply);
      await reload();
    }
  }

  const visible = useMemo(() => {
    const needle = query.trim();
    return rows.filter((row) => {
      const haystack = `${row.id} ${row.message} ${row.company_name ?? ""} ${row.client_name}`.includes(needle);
      if (!haystack) return false;
      if (filter === "open") return !row.reply_message;
      if (filter === "resolved") return Boolean(row.reply_message);
      return true;
    });
  }, [rows, query, filter]);

  const openCount = rows.filter((row) => !row.reply_message).length;
  const resolvedCount = rows.length - openCount;

  return (
    <RoleShell role="platform_admin" title={ar.complaints}>
      <section className="flex flex-col gap-3">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-surface-container text-secondary shadow-sm">
              <Icon name="support_agent" className="text-[22px]" />
            </span>
            <div>
              <h2 className="text-lg font-extrabold">{ar.ticketsTitle}</h2>
              <p className="text-xs text-secondary">{ar.ticketsSubtitle}</p>
            </div>
          </div>
          <span className="inline-flex items-center gap-1.5 rounded-full bg-surface-high px-3 py-1 text-xs font-bold text-secondary">
            <span className="h-2 w-2 rounded-full bg-primary-container" />
            {openCount} {ar.openStatus}
          </span>
        </div>
        <label className="relative">
          <Icon name="search" className="pointer-events-none absolute inset-y-0 start-0 flex h-12 w-11 items-center justify-center text-secondary text-[20px]" />
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder={ar.ticketSearch} className={`${fieldClass} h-12 ps-11`} />
        </label>
        <div className="flex gap-2 overflow-x-auto pb-1">
          {([
            ["all", ar.allItems, rows.length],
            ["open", ar.openStatus, openCount],
            ["resolved", ar.resolvedStatus, resolvedCount],
          ] as const).map(([id, label, count]) => (
            <button
              key={id}
              type="button"
              onClick={() => setFilter(id)}
              className={`inline-flex shrink-0 items-center gap-1.5 rounded-full px-4 py-2 text-sm font-bold shadow-sm ${filter === id ? "bg-secondary text-on-secondary" : "bg-surface-lowest text-secondary"}`}
            >
              {id === "open" ? <span className="h-1.5 w-1.5 rounded-full bg-error" /> : null}
              {id === "resolved" ? <span className="h-1.5 w-1.5 rounded-full bg-tertiary-container" /> : null}
              {label}
              <span className={`rounded-full px-1.5 py-0.5 text-[10px] ${filter === id ? "bg-white/20" : "bg-surface-high"}`}>{count}</span>
            </button>
          ))}
        </div>
      </section>

      {notice ? <Notice>{notice}</Notice> : null}

      <div className="flex items-center justify-between pt-1">
        <div className="flex items-center gap-2">
          <span className="h-4 w-1.5 rounded-full bg-secondary" />
          <h2 className="text-lg font-extrabold">{ar.complaintLog}</h2>
        </div>
        <span className="text-xs text-secondary">{ar.newestFirst}</span>
      </div>
      <section className="flex flex-col gap-3">
        {visible.map((row) => (
          <article key={row.id} className={`${cardClass} relative flex flex-col gap-4 overflow-hidden`}>
            <div className={`absolute inset-x-0 top-0 h-1.5 ${row.reply_message ? "bg-tertiary-container" : "bg-primary-container"}`} />
            <div className="flex items-start justify-between gap-2 pt-1">
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <h2 className="text-lg font-extrabold">#{row.id}</h2>
                  <span className="rounded-full bg-surface-container px-2.5 py-0.5 text-xs font-bold text-secondary">
                    {row.kind === "technical_support" ? ar.support : ar.complaint}
                  </span>
                </div>
                <p className="mt-0.5 text-xs text-secondary">{row.target === "company" ? ar.toCompany : ar.toPlatform}</p>
              </div>
              <span className={`inline-flex shrink-0 items-center gap-1.5 rounded-full px-3 py-1 text-xs font-bold ${row.reply_message ? "bg-tertiary/15 text-tertiary" : "bg-primary-fixed text-primary"}`}>
                <span className={`h-2 w-2 rounded-full ${row.reply_message ? "bg-tertiary-container" : "bg-primary-container"}`} />
                {row.reply_message ? ar.resolvedStatus : ar.openStatus}
              </span>
            </div>
            <div className="grid gap-2.5 sm:grid-cols-2">
              <div className="rounded-2xl bg-surface-low p-3">
                <p className="flex items-center gap-1 text-xs text-secondary"><Icon name="person" className="text-[15px]" />{ar.complainant}</p>
                <p className="mt-1 font-extrabold">{row.client_name}</p>
                {row.client_phone ? <p dir="ltr" className="text-xs font-bold text-secondary">{row.client_phone}</p> : null}
              </div>
              <div className="rounded-2xl bg-surface-low p-3">
                <p className="flex items-center gap-1 text-xs text-secondary"><Icon name="apartment" className="text-[15px]" />{ar.providerParty}</p>
                <p className="mt-1 font-extrabold">{row.company_name ?? ar.toPlatform}</p>
              </div>
            </div>
            <div className="rounded-2xl bg-surface-low p-3.5">
              <p className="flex items-center gap-1 text-sm font-bold text-primary"><Icon name="report_problem" className="text-[16px]" />{ar.complaintSubject}</p>
              <p className="mt-1 text-sm leading-relaxed">{row.message}</p>
            </div>
            <div className="flex flex-wrap items-center justify-between gap-2 rounded-xl bg-surface-high/60 px-3 py-2 text-xs text-secondary">
              <span className="inline-flex items-center gap-1.5"><Icon name="schedule" className="text-[16px]" />{when(row.created_at)}</span>
              {row.replied_at ? <span className="inline-flex items-center gap-1.5"><Icon name="sync" className="text-[16px]" />{when(row.replied_at)}</span> : null}
            </div>
            {row.reply_message ? (
              <p className="flex items-start gap-2 rounded-xl bg-tertiary/10 px-3 py-2 text-sm text-tertiary">
                <Icon name="redeem" className="text-[18px]" />
                {row.reply_message}
              </p>
            ) : (
              <form className="flex flex-col gap-2" onSubmit={(event) => reply(event, row.id)}>
                <label className="flex items-center gap-1 text-xs font-bold">
                  <Icon name="edit_note" className="text-secondary text-[15px]" />
                  {ar.officialReply}
                </label>
                <textarea name="message" required rows={2} placeholder={ar.reply} className={fieldClass} />
                <button className="inline-flex h-11 items-center justify-center gap-1.5 rounded-2xl bg-tertiary px-3 text-sm font-bold text-white" type="submit">
                  <Icon name="check_circle" className="text-[18px]" />
                  {ar.markResolved}
                </button>
              </form>
            )}
          </article>
        ))}
      </section>
    </RoleShell>
  );
}
