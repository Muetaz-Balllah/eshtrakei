"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { RoleShell } from "@/components/shell/role-shell";
import { BannerCarousel, PromoBanner } from "@/components/ui/banner-carousel";
import { EmptyState, fieldClass, Icon, Notice } from "@/components/ui/ui";
import { apiFetch, apiUrl, authHeaders, newIdempotencyKey } from "@/lib/api";
import { readCompanyId, writeCompanyId } from "@/lib/selected-company";
import { ar } from "@/messages/ar";

type Company = { id: number; name: string; description: string; phone: string };
type Package = { id: number; name: string; price: string; data_gb: number; speed_mbps: number; download_mbps?: number; upload_mbps?: number; duration_amount: number; duration_unit: string };
type Sub = { company_id: number; status: string };

const icons = ["bolt", "router", "cell_tower", "language"];

export default function StorePage() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [packages, setPackages] = useState<Package[]>([]);
  const [banners, setBanners] = useState<PromoBanner[]>([]);
  const [activeIds, setActiveIds] = useState<number[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState<Package | null>(null);
  const [coupon, setCoupon] = useState("");
  const [balance, setBalance] = useState("0.00");
  const [notice, setNotice] = useState("");
  const [toast, setToast] = useState("");
  const [invoiceId, setInvoiceId] = useState<number | null>(null);

  useEffect(() => {
    const headers = authHeaders();
    fetch(apiUrl("/api/companies"), { headers }).then(async (response) => {
      const rows: Company[] = response.ok ? await response.json() : [];
      setCompanies(rows);
      const saved = readCompanyId();
      setSelected(rows.find((row) => row.id === saved)?.id ?? rows[0]?.id ?? null);
    });
    apiFetch("/api/banners", { headers }).then(async (response) => {
      if (response.ok) setBanners(await response.json());
    });
    apiFetch("/api/subscriptions", { headers }).then(async (response) => {
      if (!response.ok) return;
      const rows: Sub[] = await response.json();
      setActiveIds(rows.filter((row) => row.status === "active").map((row) => row.company_id));
    });
    apiFetch("/api/wallet", { headers }).then(async (response) => {
      if (response.ok) setBalance((await response.json()).balance);
    });
  }, []);

  useEffect(() => {
    if (!selected) return;
    fetch(apiUrl(`/api/companies/${selected}/packages`), { headers: authHeaders() }).then(async (response) => {
      setPackages(response.ok ? await response.json() : []);
    });
  }, [selected]);

  const visibleCompanies = useMemo(() => {
    const needle = query.trim();
    return companies.filter((row) => !needle || row.name.includes(needle));
  }, [companies, query]);

  const visiblePackages = useMemo(() => {
    const needle = query.trim();
    return packages.filter((row) => !needle || row.name.includes(needle) || (companies.find((item) => item.id === selected)?.name.includes(needle) ?? false));
  }, [packages, query, companies, selected]);

  function buy(row: Package) {
    if (selected && activeIds.includes(selected)) {
      setToast(ar.activeSubBlock);
      window.setTimeout(() => setToast(""), 4500);
      return;
    }
    setOpen(row);
    setNotice("");
    setInvoiceId(null);
  }

  function choose(id: number) {
    setSelected(id);
    writeCompanyId(id);
  }

  async function pay(event: FormEvent) {
    event.preventDefault();
    if (!open || !selected) return;
    const response = await apiFetch("/api/subscriptions/purchases", {
      method: "POST",
      headers: { ...authHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({
        company_id: selected,
        package_id: open.id,
        coupon_code: coupon.trim() || null,
        idempotency_key: newIdempotencyKey(),
        pay_with_wallet: true,
      }),
    });
    const body = await response.json();
    if (!response.ok) {
      const message = body.code === "active_subscription" ? ar.activeSubBlock : body.message ?? ar.purchaseFail;
      setNotice(message);
      setToast(message);
      window.setTimeout(() => setToast(""), 4500);
      return;
    }
    setInvoiceId(body.invoice?.id ?? null);
    setNotice(body.message ?? ar.purchaseOk);
    const wallet = await apiFetch("/api/wallet", { headers: authHeaders() });
    if (wallet.ok) setBalance((await wallet.json()).balance);
  }

  async function downloadInvoice() {
    if (!invoiceId) return;
    const response = await apiFetch(`/api/invoices/${invoiceId}/pdf`, { headers: authHeaders() });
    if (!response.ok) return;
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `invoice-${invoiceId}.pdf`;
    link.click();
    URL.revokeObjectURL(url);
  }

  const company = companies.find((row) => row.id === selected);

  return (
    <RoleShell role="client" title={ar.store}>
      {toast ? <p className="fixed inset-x-4 top-24 z-[70] rounded-2xl bg-inverse-surface px-4 py-3 text-sm font-bold text-inverse-on-surface shadow-lg lg:inset-x-auto lg:end-8 lg:max-w-md">{toast}</p> : null}
      <BannerCarousel banners={banners} />
      <label className="relative">
        <Icon name="search" className="pointer-events-none absolute start-3 top-3 text-secondary text-[20px]" />
        <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder={ar.storeSearch} className={`${fieldClass} ps-11`} />
      </label>
      <div className="flex items-center justify-between px-1">
        <h2 className="font-extrabold">{ar.companies}</h2>
        <span className="text-sm font-bold text-primary">{visibleCompanies.length}</span>
      </div>
      <div className="flex gap-3 overflow-x-auto px-1 py-2">
        {visibleCompanies.map((row, index) => {
          const current = row.id === company?.id;
          const mine = activeIds.includes(row.id);
          return (
            <button
              key={row.id}
              type="button"
              onClick={() => choose(row.id)}
              className={`flex min-h-44 w-60 shrink-0 flex-col rounded-3xl bg-surface-lowest p-5 text-start shadow-[0_10px_25px_-5px_rgba(30,58,95,0.07)] transition hover:opacity-100 ${current ? "ring-2 ring-primary-container" : "opacity-90"}`}
            >
              <span className="flex items-start justify-between">
                <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-primary-container/10 text-primary-container">
                  <Icon name={icons[index % icons.length]} className="text-[26px]" />
                </span>
                {mine ? <span className="rounded-full bg-tertiary/15 px-2 py-1 text-xs font-bold text-tertiary">{ar.currentProvider}</span> : null}
              </span>
              <span className="mt-3 font-extrabold">{row.name}</span>
              <span className="mt-1 text-sm text-secondary">{row.phone}</span>
            </button>
          );
        })}
      </div>
      <div>
        <h2 className="font-extrabold">{ar.packages}</h2>
        <p className="text-sm text-secondary">{company?.name}</p>
      </div>
      {visiblePackages.length === 0 ? <EmptyState>{ar.packages}</EmptyState> : null}
      <div className="grid gap-4 lg:grid-cols-2">
        {visiblePackages.map((row) => (
          <article key={row.id} className="flex flex-col gap-4 rounded-3xl bg-surface-lowest p-5 shadow-[0_10px_25px_-5px_rgba(30,58,95,0.07)]">
            <div className="flex items-center gap-2">
              <span className="h-6 w-1.5 rounded-full bg-primary-container" />
              <h3 className="text-lg font-extrabold">{row.name}</h3>
            </div>
            <div className="grid grid-cols-3 gap-2 text-center text-sm">
              <div className="rounded-2xl bg-surface-low p-2.5">
                <p className="font-extrabold text-primary-container" dir="ltr">{row.download_mbps || row.speed_mbps}/{row.upload_mbps || row.speed_mbps}</p>
                <p className="text-xs text-secondary">{ar.downloadMbps}</p>
              </div>
              <div className="rounded-2xl bg-surface-low p-2.5">
                <p className="font-extrabold" dir="ltr">{row.data_gb} GB</p>
                <p className="text-xs text-secondary">{ar.dataGb}</p>
              </div>
              <div className="rounded-2xl bg-surface-low p-2.5">
                <p className="font-extrabold">{row.duration_amount} {ar.days}</p>
                <p className="text-xs text-secondary">{ar.duration}</p>
              </div>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-secondary">{ar.price}</p>
                <p className="text-2xl font-extrabold">{row.price} <span className="text-sm text-secondary">{ar.currency}</span></p>
              </div>
              <button type="button" className="inline-flex h-[52px] items-center gap-2 rounded-2xl bg-inverse-surface px-5 font-bold text-inverse-on-surface transition hover:opacity-90" onClick={() => buy(row)}>
                {ar.buyNow}
                <Icon name="arrow_back" className="text-[18px]" />
              </button>
            </div>
          </article>
        ))}
      </div>

      {open ? (
        <div className="fixed inset-0 z-[60] flex items-end justify-center bg-black/50 backdrop-blur-sm lg:items-center lg:p-6">
          <form onSubmit={pay} className="flex max-h-[90vh] w-full max-w-md flex-col gap-4 overflow-y-auto rounded-t-[32px] bg-surface-lowest p-5 lg:rounded-3xl">
            <div className="mx-auto h-1.5 w-12 rounded-full bg-secondary/20 lg:hidden" />
            <div className="flex items-center justify-between">
              <h2 className="flex items-center gap-2 font-extrabold"><Icon name="shopping_bag" className="text-primary-container" />{ar.buy}</h2>
              <button type="button" className="flex h-8 w-8 items-center justify-center rounded-full bg-surface-container text-secondary transition hover:bg-surface-high" onClick={() => setOpen(null)}>
                <Icon name="close" className="text-[20px]" />
              </button>
            </div>
            <div className="rounded-2xl bg-surface-low p-4">
              <div className="flex justify-between text-sm"><span className="text-secondary">{ar.packages}</span><span className="font-bold text-primary">{company?.name}</span></div>
              <div className="mt-1 flex justify-between"><h3 className="font-extrabold">{open.name}</h3><span className="font-extrabold text-primary-container">{open.price} {ar.currency}</span></div>
              <p className="mt-2 text-sm text-secondary">{open.speed_mbps} Mbps • {open.data_gb} GB</p>
            </div>
            <label className="flex flex-col gap-1.5 text-sm font-bold text-secondary">
              {ar.couponCode}
              <input value={coupon} onChange={(event) => setCoupon(event.target.value)} className={fieldClass} />
            </label>
            <div className="rounded-2xl bg-surface-low p-3">
              <p className="font-extrabold">{ar.wallet}</p>
              <p className="text-sm text-secondary">{ar.balance}: {balance} {ar.currency}</p>
              {Number(balance) < Number(open.price) ? <Link href="/client/wallet" className="mt-2 inline-block text-sm font-bold text-primary transition hover:underline">{ar.topUp}</Link> : null}
            </div>
            <button className="flex h-[52px] items-center justify-center gap-2 rounded-2xl bg-primary-container font-bold text-white transition hover:opacity-90" type="submit">
              <Icon name="check_circle" className="text-[20px]" />
              {ar.payWallet}
            </button>
            {invoiceId ? <button type="button" className="h-11 rounded-2xl bg-surface-container font-bold text-secondary transition hover:bg-surface-high" onClick={downloadInvoice}>{ar.downloadInvoice}</button> : null}
            {notice ? <Notice>{notice}</Notice> : null}
          </form>
        </div>
      ) : null}
    </RoleShell>
  );
}
