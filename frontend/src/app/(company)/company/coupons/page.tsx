"use client";

import { FormEvent, useEffect, useState } from "react";
import { RoleShell } from "@/components/shell/role-shell";
import { Badge, cardClass, dangerButton, fieldClass, primaryButton } from "@/components/ui/ui";
import { apiFetch, authHeaders } from "@/lib/api";
import { couponExhausted, couponExpired, couponExpiryIso, formatCouponDate } from "@/lib/coupons";
import { ar } from "@/messages/ar";

type Coupon = {
  id: number;
  code: string;
  discount_amount: string;
  expires_at: string;
  max_uses: number | null;
  max_total_uses: number | null;
  redemption_count: number;
};

function limitOf(row: Coupon) {
  return row.max_total_uses ?? row.max_uses;
}

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
        expires_at: couponExpiryIso(String(form.get("expires_at"))),
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
        <label className="flex flex-col gap-1 text-xs font-bold text-secondary">
          {ar.expires}
          <input name="expires_at" required type="date" className={fieldClass} />
        </label>
        <input name="max_total_uses" type="number" min="1" placeholder={ar.maxTotalUses} className={fieldClass} />
        <button className={primaryButton} type="submit">{ar.createCoupon}</button>
      </form>
      <div className="grid gap-3 lg:grid-cols-2">
        {rows.map((row) => {
          const limit = limitOf(row);
          const expired = couponExpired(row.expires_at);
          const exhausted = couponExhausted(row.redemption_count, limit);
          const remaining = limit === null ? ar.noUseLimit : String(Math.max(limit - row.redemption_count, 0));
          const status = expired ? ar.couponExpired : exhausted ? ar.couponExhausted : ar.active;
          const tone = expired || exhausted ? "bad" : "ok";
          return (
            <article key={row.id} className={`${cardClass} flex flex-col gap-4 ${expired ? "ring-2 ring-error" : ""}`}>
              <div className="flex items-start justify-between gap-3">
                <p dir="ltr" className="text-xl font-extrabold tracking-wide">{row.code}</p>
                <Badge tone={tone}>{status}</Badge>
              </div>
              <dl className="grid grid-cols-1 gap-3 text-sm sm:grid-cols-2">
                <div>
                  <dt className="text-xs font-bold text-secondary">{ar.discount}</dt>
                  <dd className="font-extrabold">{row.discount_amount} {ar.currency}</dd>
                </div>
                <div>
                  <dt className="text-xs font-bold text-secondary">{ar.expires}</dt>
                  <dd className={`font-bold ${expired ? "text-error" : ""}`}>{formatCouponDate(row.expires_at)}</dd>
                </div>
                <div>
                  <dt className="text-xs font-bold text-secondary">{ar.usedTimes}</dt>
                  <dd className="font-bold">{row.redemption_count}</dd>
                </div>
                <div>
                  <dt className="text-xs font-bold text-secondary">{ar.maxTotalUses}</dt>
                  <dd className="font-bold">{limit ?? ar.noUseLimit}</dd>
                </div>
                <div>
                  <dt className="text-xs font-bold text-secondary">{ar.remainingUses}</dt>
                  <dd className="font-bold">{remaining}</dd>
                </div>
              </dl>
              <button type="button" className={`${dangerButton} w-full sm:w-fit`} onClick={() => remove(row.id)}>{ar.remove}</button>
            </article>
          );
        })}
      </div>
    </RoleShell>
  );
}
