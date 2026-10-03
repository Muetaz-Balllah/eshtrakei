"use client";

import { FormEvent, useEffect, useState } from "react";
import { RoleShell } from "@/components/shell/role-shell";
import { fieldClass, Icon, Notice } from "@/components/ui/ui";
import { apiFetch, authHeaders } from "@/lib/api";
import { ar } from "@/messages/ar";

type Tx = { id: number; amount: string; kind: string; note: string; created_at: string };
type Wallet = { balance: string; currency: string; transactions: Tx[] };

const presets = ["20", "50", "100", "200"];

export default function WalletPage() {
  const [wallet, setWallet] = useState<Wallet | null>(null);
  const [amount, setAmount] = useState("50");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);

  async function reload() {
    const response = await apiFetch("/api/wallet", { headers: authHeaders() });
    if (response.ok) setWallet(await response.json());
  }

  useEffect(() => {
    reload();
  }, []);

  async function topUp(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setNotice("");
    const response = await apiFetch("/api/wallet/topups", {
      method: "POST",
      headers: { ...authHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({ amount, simulated_outcome: "success" }),
    });
    const body = await response.json();
    setBusy(false);
    if (!response.ok) {
      setNotice(body.message ?? ar.purchaseFail);
      return;
    }
    setWallet(body);
    setNotice(ar.purchaseOk);
  }

  return (
    <RoleShell role="client" title={ar.wallet}>
      <section className="flex flex-col gap-4 rounded-3xl bg-primary-container p-5 text-white shadow-[0_12px_28px_-6px_rgba(245,130,32,0.35)]">
        <div className="flex items-center justify-between">
          <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white/20"><Icon name="account_balance_wallet" /></span>
          <div className="text-end">
            <p className="text-sm text-white/85">{ar.balance}</p>
            <p className="text-4xl font-extrabold">{wallet?.balance ?? "0.00"} <span className="text-lg">{ar.currency}</span></p>
          </div>
        </div>
      </section>
      <form onSubmit={topUp} className="flex flex-col gap-3 rounded-3xl bg-surface-lowest p-5 shadow-[0_10px_25px_-5px_rgba(30,58,95,0.07)]">
        <h2 className="font-extrabold">{ar.topUp}</h2>
        <div className="grid grid-cols-4 gap-2">
          {presets.map((value) => (
            <button key={value} type="button" onClick={() => setAmount(value)} className={`h-11 rounded-2xl text-sm font-bold ${amount === value ? "bg-inverse-surface text-inverse-on-surface" : "bg-surface-low text-secondary"}`}>
              {value}
            </button>
          ))}
        </div>
        <input className={fieldClass} required type="number" min="0.01" step="0.01" value={amount} onChange={(event) => setAmount(event.target.value)} placeholder={ar.topUp} />
        <button disabled={busy} className="flex h-12 items-center justify-center gap-2 rounded-2xl bg-surface font-bold text-primary-container shadow-sm disabled:opacity-60" type="submit">
          <Icon name="add" className="text-[20px]" />
          {ar.topUp}
        </button>
        {notice ? <Notice>{notice}</Notice> : null}
      </form>
      <section className="flex flex-col gap-3">
        <h2 className="px-1 font-extrabold">{ar.invoices}</h2>
        {(wallet?.transactions ?? []).map((row) => {
          const positive = row.kind === "topup";
          return (
            <article key={row.id} className="flex items-center justify-between rounded-2xl bg-surface-lowest p-4 shadow-sm">
              <div>
                <p className="font-bold">{row.note || (row.kind === "topup" ? ar.topUp : ar.payWallet)}</p>
                <p className="text-sm text-secondary">{new Date(row.created_at).toLocaleString("ar")}</p>
              </div>
              <p className={`font-extrabold ${positive ? "text-tertiary" : ""}`}>{positive ? "+" : "-"}{row.amount} {ar.currency}</p>
            </article>
          );
        })}
      </section>
    </RoleShell>
  );
}
