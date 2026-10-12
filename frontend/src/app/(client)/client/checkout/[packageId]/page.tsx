"use client";

import { useParams, useSearchParams } from "next/navigation";
import { useState } from "react";
import { RoleShell } from "@/components/shell/role-shell";
import { cardClass, dangerButton, fieldClass, ghostButton, Notice, primaryButton } from "@/components/ui/ui";
import { apiFetch, authHeaders, newIdempotencyKey } from "@/lib/api";
import { ar } from "@/messages/ar";

export default function CheckoutPage() {
  const params = useParams<{ packageId: string }>();
  const search = useSearchParams();
  const [coupon, setCoupon] = useState("");
  const [message, setMessage] = useState("");
  const [invoiceId, setInvoiceId] = useState<number | null>(null);

  async function downloadInvoice(id: number) {
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

  async function pay(outcome: "success" | "failure" | "wallet") {
    const response = await apiFetch("/api/subscriptions/purchases", {
      method: "POST",
      headers: { ...authHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({
        company_id: Number(search.get("company")),
        package_id: Number(params.packageId),
        coupon_code: coupon.trim() || null,
        idempotency_key: newIdempotencyKey(),
        simulated_outcome: outcome === "wallet" ? "success" : outcome,
        pay_with_wallet: outcome === "wallet",
      }),
    });
    const body = await response.json();
    if (!response.ok) {
      setMessage(body.message ?? ar.purchaseFail);
      return;
    }
    if (body.payment_status === "succeeded") {
      setInvoiceId(body.invoice.id);
      setMessage(`${ar.purchaseOk} — ${ar.invoiceNo} ${body.invoice.invoice_number}`);
      return;
    }
    setMessage(body.message ?? ar.purchaseFail);
  }

  return (
    <RoleShell role="client" title={ar.buy}>
      <section className={`${cardClass} mx-auto flex w-full max-w-xl flex-col gap-4`}>
        <label className="flex flex-col gap-2 text-sm font-bold text-secondary">
          {ar.couponCode}
          <input value={coupon} onChange={(event) => setCoupon(event.target.value)} className={fieldClass} />
        </label>
        <div className="grid gap-3 sm:grid-cols-2">
          <button type="button" className={primaryButton} onClick={() => pay("success")}>{ar.paySuccess}</button>
          <button type="button" className={primaryButton} onClick={() => pay("wallet")}>{ar.payWallet}</button>
          <button type="button" className={dangerButton} onClick={() => pay("failure")}>{ar.payFail}</button>
        </div>
        {message ? <Notice>{message}</Notice> : null}
        {invoiceId ? (
          <button type="button" className={ghostButton} onClick={() => downloadInvoice(invoiceId)}>
            {ar.downloadInvoice}
          </button>
        ) : null}
      </section>
    </RoleShell>
  );
}
