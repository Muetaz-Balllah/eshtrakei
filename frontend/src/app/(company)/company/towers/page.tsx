"use client";

import { FormEvent, useEffect, useState } from "react";
import { CoverageMap, MapTower } from "@/components/map/coverage-map";
import { RoleShell } from "@/components/shell/role-shell";
import { cardClass, dangerButton, fieldClass, Notice, primaryButton } from "@/components/ui/ui";
import { apiFetch, authHeaders } from "@/lib/api";
import { ar } from "@/messages/ar";

export default function TowersPage() {
  const [rows, setRows] = useState<MapTower[]>([]);
  const [point, setPoint] = useState({ latitude: 32.8872, longitude: 13.1913 });
  const [notice, setNotice] = useState("");

  async function reload() {
    const response = await apiFetch("/api/company/towers", { headers: authHeaders() });
    if (response.ok) setRows(await response.json());
  }

  useEffect(() => {
    reload();
  }, []);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    const response = await apiFetch("/api/company/towers", {
      method: "POST",
      headers: { ...authHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({
        name: form.get("name"),
        latitude: point.latitude,
        longitude: point.longitude,
        radius_meters: Number(form.get("radius_meters")),
      }),
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) {
      setNotice(body.message ?? ar.purchaseFail);
      return;
    }
    setNotice(ar.save);
    formElement.reset();
    await reload();
  }

  async function remove(id: number) {
    await apiFetch(`/api/company/towers/${id}`, { method: "DELETE", headers: authHeaders() });
    await reload();
  }

  return (
    <RoleShell role="company_manager" title={ar.towers}>
      <p className="px-1 text-sm text-secondary">{ar.clickMap}</p>
      <CoverageMap towers={rows} onPick={(latitude, longitude) => setPoint({ latitude, longitude })} />
      {notice ? <Notice>{notice}</Notice> : null}
      <form onSubmit={onSubmit} className={`${cardClass} grid gap-3 lg:grid-cols-4`}>
        <input name="name" required placeholder={ar.towerName} className={fieldClass} />
        <input className={fieldClass} readOnly value={point.latitude.toFixed(5)} />
        <input className={fieldClass} readOnly value={point.longitude.toFixed(5)} />
        <input name="radius_meters" required type="number" min="50" placeholder="متر" className={fieldClass} />
        <button className={`${primaryButton} lg:col-span-4 lg:w-fit`} type="submit">{ar.save}</button>
      </form>
      <div className="grid gap-3 lg:grid-cols-2">
        {rows.map((row) => (
          <article key={row.id} className={`${cardClass} flex items-center justify-between`}>
            <div>
              <h2 className="font-extrabold">{row.name}</h2>
              <p className="text-sm text-secondary" dir="ltr">{row.radius_meters} m</p>
            </div>
            <button type="button" className={dangerButton} onClick={() => remove(row.id)}>{ar.remove}</button>
          </article>
        ))}
      </div>
    </RoleShell>
  );
}
