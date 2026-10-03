"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { RoleShell } from "@/components/shell/role-shell";
import { BannerCarousel, PromoBanner } from "@/components/ui/banner-carousel";
import { QuotaRing } from "@/components/ui/quota-ring";
import { EmptyState, Icon, Notice } from "@/components/ui/ui";
import { apiFetch, apiUrl, authHeaders } from "@/lib/api";
import { readCompanyId, writeCompanyId } from "@/lib/selected-company";
import { ar } from "@/messages/ar";

type Company = { id: number; name: string; phone: string };
type Me = { full_name: string; avatar_url: string | null };
type Sub = {
  id: number;
  company_id: number;
  company_name: string;
  package_name: string;
  status: string;
  end_date: string;
  days_remaining: number;
  price: string;
  data_gb: number;
  speed_mbps: number;
  upload_mbps: number;
};
type Tx = { id: number; amount: string; kind: string; note: string; created_at: string };
type Invoice = { id: number; package_name: string; amount_paid: string; issued_at: string | null };
type Activity = { id: string; title: string; when: string; amount: string; positive: boolean };

export default function ClientHomePage() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [banners, setBanners] = useState<PromoBanner[]>([]);
  const [me, setMe] = useState<Me | null>(null);
  const [subs, setSubs] = useState<Sub[]>([]);
  const [walletBalance, setWalletBalance] = useState("0.00");
  const [activity, setActivity] = useState<Activity[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [notice, setNotice] = useState("");

  useEffect(() => {
    const headers = authHeaders();
    Promise.all([
      fetch(apiUrl("/api/companies"), { headers }),
      apiFetch("/api/auth/me", { headers }),
      apiFetch("/api/subscriptions", { headers }),
      apiFetch("/api/wallet", { headers }),
      apiFetch("/api/invoices", { headers }),
    ]).then(async ([companyResponse, meResponse, subResponse, walletResponse, invoiceResponse]) => {
      const companyRows: Company[] = companyResponse.ok ? await companyResponse.json() : [];
      setCompanies(companyRows);
      const saved = readCompanyId();
      const initial = companyRows.find((row) => row.id === saved)?.id ?? companyRows[0]?.id ?? null;
      setSelected(initial);
      apiFetch("/api/banners", { headers }).then(async (response) => {
        if (response.ok) setBanners(await response.json());
      });
      if (meResponse.ok) setMe(await meResponse.json());
      if (subResponse.ok) setSubs(await subResponse.json());
      const wallet = walletResponse.ok ? await walletResponse.json() : { balance: "0.00", transactions: [] };
      setWalletBalance(wallet.balance ?? "0.00");
      const invoices: Invoice[] = invoiceResponse.ok ? await invoiceResponse.json() : [];
      const fromWallet = (wallet.transactions ?? []).map((row: Tx) => ({
        id: `w-${row.id}`,
        title: row.note || (row.kind === "topup" ? ar.topUp : ar.payWallet),
        when: new Date(row.created_at).toLocaleDateString("ar"),
        amount: `${row.kind === "topup" ? "+" : "-"}${row.amount}`,
        positive: row.kind === "topup",
        sort: row.created_at,
      }));
      const fromInvoices = invoices.map((row) => ({
        id: `i-${row.id}`,
        title: row.package_name,
        when: row.issued_at ? new Date(row.issued_at).toLocaleDateString("ar") : "",
        amount: row.amount_paid,
        positive: false,
        sort: row.issued_at ?? "",
      }));
      const merged = [...fromWallet, ...fromInvoices]
        .sort((left, right) => right.sort.localeCompare(left.sort))
        .slice(0, 5)
        .map(({ sort: _sort, ...row }) => row);
      setActivity(merged);
    });
  }, []);

  function choose(id: number) {
    setSelected(id);
    writeCompanyId(id);
  }

  const forCompany = (companyId: number) =>
    subs.find((sub) => sub.company_id === companyId && sub.status === "active") ??
    subs.find((sub) => sub.company_id === companyId && sub.status === "expired");
  const subscribed = companies.filter((row) => forCompany(row.id));
  const company = subscribed.find((row) => row.id === selected) ?? subscribed[0];
  const subscription = company ? forCompany(company.id) : undefined;
  const showRenew = subscription?.status === "expired";

  async function renew() {
    if (!subscription) return;
    const response = await apiFetch(`/api/subscriptions/${subscription.id}/renew`, {
      method: "POST",
      headers: { ...authHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({ idempotency_key: crypto.randomUUID(), pay_with_wallet: true }),
    });
    const body = await response.json();
    setNotice(response.ok ? body.message : body.message ?? ar.purchaseFail);
    if (response.ok) {
      const wallet = await apiFetch("/api/wallet", { headers: authHeaders() });
      if (wallet.ok) setWalletBalance((await wallet.json()).balance);
    }
  }

  return (
    <RoleShell role="client" title={ar.clientHome}>
      <section className="flex items-center justify-between rounded-3xl bg-surface-lowest p-4 shadow-[0_10px_25px_-5px_rgba(30,58,95,0.07)]">
        <div className="flex items-center gap-3">
          {me?.avatar_url ? (
            <img src={apiUrl(me.avatar_url)} alt="" className="h-14 w-14 rounded-full object-cover ring-2 ring-primary-container/20" />
          ) : (
            <span className="flex h-14 w-14 items-center justify-center rounded-full bg-surface-container text-secondary ring-2 ring-primary-container/20">
              <Icon name="person" className="text-[28px]" />
            </span>
          )}
          <div>
            <h2 className="font-extrabold">{me?.full_name}</h2>
            <span className="mt-1 inline-flex items-center gap-1.5 rounded-full bg-tertiary/15 px-2.5 py-0.5 text-xs font-bold text-tertiary">
              <span className="h-2 w-2 rounded-full bg-tertiary" />
              {ar.active}
            </span>
          </div>
        </div>
        <Link href="/client/notifications" aria-label={ar.notifications} className="relative flex h-11 w-11 items-center justify-center rounded-2xl bg-surface-low text-secondary">
          <Icon name="notifications" className="text-[22px]" />
          <span className="absolute top-2 start-2 h-2 w-2 rounded-full bg-primary-container" />
        </Link>
      </section>

      <BannerCarousel banners={banners} />

      <section className="flex flex-col gap-2">
        <span className="px-1 text-sm font-bold text-secondary">{ar.companies}</span>
        {subscribed.length === 0 ? <EmptyState>{ar.noActiveSubscriptions}</EmptyState> : null}
        <div className="flex gap-2 overflow-x-auto pb-1">
          {subscribed.map((row) => {
            const active = row.id === company?.id;
            return (
              <button key={row.id} type="button" onClick={() => choose(row.id)} className={`inline-flex shrink-0 items-center gap-2 rounded-2xl px-4 py-2 text-sm font-bold shadow-sm ${active ? "bg-inverse-surface text-inverse-on-surface" : "bg-surface-lowest text-secondary"}`}>
                <span className={`h-2 w-2 rounded-full ${active ? "bg-primary-container" : "bg-surface-container"}`} />
                {row.name}
              </button>
            );
          })}
        </div>
      </section>

      {subscription ? (
        <article className="flex flex-col gap-4 rounded-3xl bg-surface-lowest p-5 shadow-[0_10px_25px_-5px_rgba(30,58,95,0.07)]">
          <div className="flex items-center justify-end gap-2">
            <h2 className="font-extrabold" dir="ltr">{subscription.package_name} ({subscription.price})</h2>
            <span className="h-6 w-1.5 rounded-full bg-primary-container" />
          </div>
          <QuotaRing totalGb={subscription.data_gb} />
          <div className="flex items-center justify-between rounded-2xl bg-surface-low p-4">
            <div>
              <p className="text-sm text-secondary">{ar.daysLeft}</p>
              <p className="text-lg font-extrabold">{subscription.days_remaining > 0 ? subscription.days_remaining : ar.expired}</p>
            </div>
            <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-surface-lowest text-secondary"><Icon name="timer" /></span>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="rounded-2xl bg-surface-low p-3 text-center">
              <Icon name="calendar_today" className="text-secondary text-[18px]" />
              <p className="mt-1 text-xs text-secondary">{ar.expires}</p>
              <p className="text-sm font-bold" dir="ltr">{subscription.end_date}</p>
            </div>
            <div className="rounded-2xl bg-surface-low p-3 text-center">
              <Icon name="bolt" className="text-secondary text-[18px]" />
              <p className="mt-1 text-xs text-secondary">{ar.dataGb}</p>
              <p className="text-sm font-bold" dir="ltr">GB {subscription.data_gb}</p>
            </div>
          </div>
          {showRenew ? (
            <button type="button" onClick={renew} className="flex h-14 items-center justify-center gap-2 rounded-2xl bg-inverse-surface font-bold text-inverse-on-surface transition hover:opacity-90">
              {ar.renew}
              <Icon name="refresh" className="text-[20px]" />
            </button>
          ) : null}
          {notice ? <Notice>{notice}</Notice> : null}
        </article>
      ) : null}

      <div className="grid grid-cols-2 gap-3">
        <article className="flex h-36 flex-col justify-between rounded-3xl bg-inverse-surface p-5 text-inverse-on-surface">
          <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-white/15"><Icon name="arrow_downward" className="text-[20px]" /></span>
          <div className="text-center">
            <p className="text-xs opacity-80">التحميل</p>
            <p className="text-lg font-extrabold" dir="ltr">Mbps {subscription?.speed_mbps ?? 0}</p>
          </div>
        </article>
        <article className="flex h-36 flex-col justify-between rounded-3xl bg-primary-container p-5 text-white">
          <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-white/25"><Icon name="arrow_upward" className="text-[20px]" /></span>
          <div className="text-center">
            <p className="text-xs text-white/80">الرفع</p>
            <p className="text-lg font-extrabold" dir="ltr">Mbps {subscription?.upload_mbps || subscription?.speed_mbps || 0}</p>
          </div>
        </article>
      </div>

      <section className="flex flex-col gap-4 rounded-3xl bg-primary-container p-5 text-white shadow-[0_12px_28px_-6px_rgba(245,130,32,0.35)]">
        <div className="flex items-center justify-between">
          <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white/20"><Icon name="account_balance_wallet" /></span>
          <div className="text-end">
            <p className="text-sm text-white/85">{ar.balance}</p>
            <p className="text-3xl font-extrabold">{walletBalance} <span className="text-lg">{ar.currency}</span></p>
          </div>
        </div>
        <Link href="/client/wallet" className="flex h-12 items-center justify-center gap-2 rounded-2xl bg-surface font-bold text-primary-container">
          <Icon name="add" className="text-[20px]" />
          {ar.topUp}
        </Link>
      </section>

      <section className="flex flex-col gap-3">
        <div className="flex items-center justify-between px-1">
          <h3 className="font-extrabold">{ar.invoices}</h3>
          <Link href="/client/wallet" className="text-sm font-bold text-secondary">{ar.sales}</Link>
        </div>
        {activity.map((row) => (
          <article key={row.id} className="flex items-center justify-between rounded-2xl bg-surface-lowest p-4 shadow-sm">
            <div className="flex items-center gap-3">
              <span className={`flex h-11 w-11 items-center justify-center rounded-xl ${row.positive ? "bg-primary/10 text-primary-container" : "bg-tertiary/15 text-tertiary"}`}>
                <Icon name={row.positive ? "add_card" : "wifi"} className="text-[20px]" />
              </span>
              <div>
                <p className="font-bold">{row.title}</p>
                <p className="text-sm text-secondary">{row.when}</p>
              </div>
            </div>
            <p className={`font-extrabold ${row.positive ? "text-tertiary" : ""}`}>{row.amount} {ar.currency}</p>
          </article>
        ))}
      </section>
    </RoleShell>
  );
}
