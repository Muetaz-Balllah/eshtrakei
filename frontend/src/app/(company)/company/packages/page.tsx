"use client";

import { FormEvent, useEffect, useState } from "react";
import { RoleShell } from "@/components/shell/role-shell";
import { Badge, cardClass, dangerButton, fieldClass, ghostButton, primaryButton, SectionTitle } from "@/components/ui/ui";
import { apiFetch, authHeaders } from "@/lib/api";
import { ar } from "@/messages/ar";

type Package = {
  id: number;
  name: string;
  price: string;
  duration_amount: number;
  duration_unit: "days" | "months";
  data_gb: number;
  speed_mbps: number;
  download_mbps: number;
  upload_mbps: number;
  is_available: boolean;
};

export default function PackagesPage() {
  const [rows, setRows] = useState<Package[]>([]);
  const [editing, setEditing] = useState<Package | null>(null);
  const [formVersion, setFormVersion] = useState(0);

  async function reload() {
    const response = await apiFetch("/api/company/packages", { headers: authHeaders() });
    if (response.ok) setRows(await response.json());
  }

  useEffect(() => {
    reload();
  }, []);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const body = {
      name: form.get("name"),
      price: form.get("price"),
      duration_amount: Number(form.get("duration_amount")),
      duration_unit: "days",
      data_gb: Number(form.get("data_gb")),
      download_mbps: Number(form.get("download_mbps")),
      upload_mbps: Number(form.get("upload_mbps")),
    };
    const path = editing ? `/api/company/packages/${editing.id}` : "/api/company/packages";
    await apiFetch(path, {
      method: editing ? "PATCH" : "POST",
      headers: { ...authHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    setEditing(null);
    setFormVersion((version) => version + 1);
    await reload();
  }

  async function resume(id: number) {
    await apiFetch(`/api/company/packages/${id}/resume`, { method: "POST", headers: authHeaders() });
    await reload();
  }

  async function stop(id: number) {
    await apiFetch(`/api/company/packages/${id}/stop`, { method: "POST", headers: authHeaders() });
    await reload();
  }

  async function remove(id: number) {
    await apiFetch(`/api/company/packages/${id}`, { method: "DELETE", headers: authHeaders() });
    await reload();
  }

  return (
    <RoleShell role="company_manager" title={ar.packages}>
      <form key={`${editing?.id ?? "new"}-${formVersion}`} onSubmit={onSubmit} className={`${cardClass} grid gap-3 md:grid-cols-2 xl:grid-cols-3`}>
        <SectionTitle className="md:col-span-2 xl:col-span-3">{editing ? ar.save : ar.packages}</SectionTitle>
        <input name="name" required placeholder={ar.packageName} defaultValue={editing?.name} className={`${fieldClass} md:col-span-2 xl:col-span-3`} />
        <input name="price" required type="number" min="0.01" step="0.01" placeholder={ar.price} defaultValue={editing?.price} className={fieldClass} />
        <input name="duration_amount" required type="number" min="1" placeholder={`${ar.duration} (${ar.days})`} defaultValue={editing?.duration_amount} className={fieldClass} />
        <input name="data_gb" required type="number" min="1" placeholder={ar.dataGb} defaultValue={editing?.data_gb} className={fieldClass} />
        <input name="download_mbps" required type="number" min="1" placeholder={ar.downloadMbps} defaultValue={editing?.download_mbps ?? editing?.speed_mbps} className={fieldClass} />
        <input name="upload_mbps" required type="number" min="1" placeholder={ar.uploadMbps} defaultValue={editing?.upload_mbps ?? editing?.speed_mbps} className={fieldClass} />
        <button className={primaryButton} type="submit">{ar.save}</button>
      </form>
      <div className="grid gap-4 lg:grid-cols-2">
        {rows.map((row) => (
          <article key={row.id} className={`${cardClass} flex flex-col gap-4`}>
            <div className="flex items-start justify-between gap-3">
              <div>
                <h2 className="text-lg font-extrabold">{row.name}</h2>
                <p className="text-sm text-secondary">{row.duration_amount} {ar.days}</p>
              </div>
              <span className="text-2xl font-extrabold text-primary-container">{row.price} <span className="text-sm">{ar.currency}</span></span>
            </div>
            <div className="flex flex-wrap gap-2">
              <Badge tone={row.is_available ? "ok" : "neutral"}>{row.is_available ? ar.available : ar.hidden}</Badge>
              <Badge>{row.data_gb} GB</Badge>
              <Badge>{ar.downloadMbps} {row.download_mbps || row.speed_mbps}</Badge>
              <Badge>{ar.uploadMbps} {row.upload_mbps || row.speed_mbps}</Badge>
            </div>
            <div className="flex flex-wrap gap-2">
              <button type="button" className={ghostButton} onClick={() => setEditing(row)}>{ar.save}</button>
              {row.is_available ? (
                <button type="button" className={ghostButton} onClick={() => stop(row.id)}>{ar.hidePackage}</button>
              ) : (
                <button type="button" className={ghostButton} onClick={() => resume(row.id)}>{ar.resumePackage}</button>
              )}
              <button type="button" className={dangerButton} onClick={() => remove(row.id)}>{ar.remove}</button>
            </div>
          </article>
        ))}
      </div>
    </RoleShell>
  );
}
