"use client";

import { FormEvent, useEffect, useState } from "react";
import { RoleShell } from "@/components/shell/role-shell";
import { cardClass, dangerButton, fieldClass, primaryButton } from "@/components/ui/ui";
import { apiFetch, authHeaders } from "@/lib/api";
import { ar } from "@/messages/ar";

type Coupon = { id: number; code: string; discount_amount: string; expires_at: string; max_total_uses: number | null; redemption_count: number };

export default function CouponsPage() {
  const [rows, setRows] = useState<Coupon[]>([]);

  async function reload() {
    const response = await apiFetch("/api/company/coupons", { headers: authHeaders() });
    if (response.ok) setRows(await response.json());
  }

  useEffect(() => {
    reload();
  }, []);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    await apiFetch("/api/company/coupons", {
      method: "POST",
      headers: { ...authHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({
        code: form.get("code"),
        discount_amount: form.get("discount_amount"),
        expires_at: new Date(String(form.get("expires_at"))).toISOString(),
        max_total_uses: form.get("max_total_uses") ? Number(form.get("max_total_uses")) : null,
      }),
    });
    formElement.reset();
    await reload();
  }

  async function remove(id: number) {
    await apiFetch(`/api/company/coupons/${id}`, { method: "DELETE", headers: authHeaders() });
    await reload();
  }

  return (
    <RoleShell role="company_manager" title={ar.coupons}>
      <form onSubmit={onSubmit} className={`${cardClass} grid gap-3 md:grid-cols-2 xl:grid-cols-4`}>
        <input name="code" required placeholder={ar.couponCode} className={fieldClass} />
        <input name="discount_amount" required type="number" min="0.01" step="0.01" placeholder={ar.discount} className={fieldClass} />
        <input name="expires_at" required type="date" className={fieldClass} />
        <input name="max_total_uses" type="number" min="1" placeholder={ar.maxTotalUses} className={fieldClass} />
        <button className={primaryButton} type="submit">{ar.createCoupon}</button>
      </form>
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {rows.map((row) => (
          <article key={row.id} className="rounded-3xl bg-inverse-surface p-5 text-inverse-on-surface shadow-md">
            <p dir="ltr" className="text-xl font-extrabold tracking-wide">{row.code}</p>
            <p className="mt-2 text-2xl font-extrabold text-primary-fixed">{row.discount_amount} {ar.currency}</p>
            <p className="mt-1 text-sm text-[#d5e3ff]">{new Date(row.expires_at).toLocaleDateString("ar")}</p>
            <p className="mt-2 text-sm">{ar.usedTimes}: {row.redemption_count}{row.max_total_uses ? ` / ${row.max_total_uses}` : ""}</p>
            <button type="button" className={`${dangerButton} mt-3`} onClick={() => remove(row.id)}>{ar.remove}</button>
          </article>
        ))}
      </div>
    </RoleShell>
  );
}
