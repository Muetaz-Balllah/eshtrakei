"use client";

import { FormEvent, useEffect, useState } from "react";
import { RoleShell } from "@/components/shell/role-shell";
import { cardClass, fieldClass, primaryButton, SectionTitle } from "@/components/ui/ui";
import { apiFetch, authHeaders } from "@/lib/api";
import { ar } from "@/messages/ar";

type Company = { id: number; name: string };
type Complaint = { id: number; kind: string; message: string; reply_message: string | null; company_name: string | null };

export default function ComplaintsPage() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [rows, setRows] = useState<Complaint[]>([]);
  const [target, setTarget] = useState("company");
  const [supportEmail, setSupportEmail] = useState("");

  async function reload() {
    const headers = authHeaders();
    const companyResponse = await apiFetch("/api/complaints/companies", { headers });
    if (companyResponse.ok) setCompanies(await companyResponse.json());
    const list = await apiFetch("/api/complaints", { headers });
    if (list.ok) setRows(await list.json());
    const support = await apiFetch("/api/settings/support-email", { headers });
    if (support.ok) setSupportEmail((await support.json()).support_email);
  }

  useEffect(() => {
    reload();
  }, []);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    await apiFetch("/api/complaints", {
      method: "POST",
      headers: { ...authHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({
        kind: form.get("kind"),
        target: form.get("target"),
        company_id: form.get("target") === "company" ? Number(form.get("company_id")) : null,
        message: form.get("message"),
      }),
    });
    formElement.reset();
    await reload();
  }

  return (
    <RoleShell role="client" title={ar.complaints}>
      {supportEmail ? <p className="text-sm font-semibold text-secondary" dir="ltr">{ar.supportEmail}: {supportEmail}</p> : null}
      <form onSubmit={onSubmit} className={`${cardClass} grid gap-3 lg:grid-cols-2`}>
        <select name="kind" className={fieldClass}>
          <option value="complaint">{ar.complaint}</option>
          <option value="technical_support">{ar.support}</option>
        </select>
        <select name="target" className={fieldClass} value={target} onChange={(event) => setTarget(event.target.value)}>
          <option value="company">{ar.toCompany}</option>
          <option value="platform">{ar.toPlatform}</option>
        </select>
        {target === "company" ? (
          <select name="company_id" className={`${fieldClass} lg:col-span-2`}>
            {companies.map((company) => (
              <option key={company.id} value={company.id}>{company.name}</option>
            ))}
          </select>
        ) : null}
        <textarea name="message" required rows={4} className={`${fieldClass} lg:col-span-2`} />
        <button className={`${primaryButton} lg:col-span-2 lg:w-fit`} type="submit">{ar.send}</button>
      </form>
      <SectionTitle>{ar.complaints}</SectionTitle>
      <div className="grid gap-3 lg:grid-cols-2">
        {rows.map((row) => (
          <article key={row.id} className={`${cardClass} flex flex-col gap-2`}>
            <p className="text-sm font-bold text-secondary">{row.company_name}</p>
            <p className="font-semibold">{row.message}</p>
            <p className="rounded-2xl bg-surface-low px-3 py-2 text-sm text-secondary">{row.reply_message ?? ar.noReply}</p>
          </article>
        ))}
      </div>
    </RoleShell>
  );
}
