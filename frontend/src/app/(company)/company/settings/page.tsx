"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { InlineAccount } from "@/components/account/inline-account";
import { RoleShell, useLogout } from "@/components/shell/role-shell";
import { cardClass, fieldClass, Icon, Notice, primaryButton } from "@/components/ui/ui";
import { apiFetch, apiUrl, authHeaders } from "@/lib/api";
import { ar } from "@/messages/ar";

type Company = { name: string; description: string; phone: string; balance: string };
type Me = { full_name: string; phone: string | null; avatar_url: string | null };
type Report = { monthly_target: string };
type Support = { id: number; message: string; reply_message: string | null };
type Banner = { id: number; title: string; body: string; status: string; price: string };
type Ledger = { id: number; amount: string; note: string; kind: string; created_at: string };
type Panel = "company" | "banners" | "support" | null;

const rowClass = "flex w-full items-center justify-between gap-3 rounded-2xl p-3 text-start transition hover:bg-surface-low";

export default function CompanySettingsPage() {
  const logout = useLogout();
  const [company, setCompany] = useState<Company | null>(null);
  const [me, setMe] = useState<Me | null>(null);
  const [report, setReport] = useState<Report | null>(null);
  const [messages, setMessages] = useState<Support[]>([]);
  const [banners, setBanners] = useState<Banner[]>([]);
  const [price, setPrice] = useState("0");
  const [ledger, setLedger] = useState<Ledger[]>([]);
  const [panel, setPanel] = useState<Panel>(null);
  const [topUp, setTopUp] = useState(false);
  const [notice, setNotice] = useState("");

  async function reload() {
    const headers = authHeaders();
    const [companyResponse, meResponse, reportResponse, supportResponse, bannerResponse, priceResponse, ledgerResponse] = await Promise.all([
      apiFetch("/api/company/me", { headers }),
      apiFetch("/api/auth/me", { headers }),
      apiFetch("/api/company/reports/sales", { headers }),
      apiFetch("/api/company/support", { headers }),
      apiFetch("/api/company/banners", { headers }),
      apiFetch("/api/company/banner-price", { headers }),
      apiFetch("/api/company/ledger", { headers }),
    ]);
    if (companyResponse.ok) setCompany(await companyResponse.json());
    if (meResponse.ok) setMe(await meResponse.json());
    if (reportResponse.ok) setReport(await reportResponse.json());
    if (supportResponse.ok) setMessages(await supportResponse.json());
    if (bannerResponse.ok) setBanners(await bannerResponse.json());
    if (priceResponse.ok) setPrice(String((await priceResponse.json()).price));
    if (ledgerResponse.ok) setLedger(await ledgerResponse.json());
  }

  useEffect(() => {
    reload();
  }, []);

  function toggle(next: Panel) {
    setPanel(panel === next ? null : next);
    setNotice("");
  }

  async function addBalance(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const response = await apiFetch("/api/company/balance/topups", {
      method: "POST",
      headers: { ...authHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({ amount: new FormData(form).get("amount"), simulated_outcome: "success" }),
    });
    const body = await response.json().catch(() => ({}));
    setNotice(body.message ?? ar.purchaseFail);
    if (response.ok) {
      form.reset();
      setTopUp(false);
      await reload();
    }
  }

  async function saveCompany(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const headers = { ...authHeaders(), "Content-Type": "application/json" };
    const response = await apiFetch("/api/company/me", {
      method: "PUT",
      headers,
      body: JSON.stringify({ name: form.get("name"), description: form.get("description"), phone: form.get("phone") }),
    });
    const target = await apiFetch("/api/company/sales-target", {
      method: "PUT",
      headers,
      body: JSON.stringify({ monthly_sales_target: form.get("monthly_sales_target") }),
    });
    if (response.ok && target.ok) {
      setNotice(ar.save);
      setPanel(null);
      await reload();
    }
  }

  async function sendSupport(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const response = await apiFetch("/api/company/support", {
      method: "POST",
      headers: { ...authHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({ message: new FormData(form).get("message") }),
    });
    if (response.ok) {
      form.reset();
      setNotice(ar.send);
      await reload();
    }
  }

  async function createBanner(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const response = await fetch(apiUrl("/api/company/banners"), { method: "POST", headers: authHeaders(), body: new FormData(form) });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) {
      setNotice(body.message ?? ar.purchaseFail);
      return;
    }
    form.reset();
    setNotice(ar.bannerPending);
    await reload();
  }

  const photo = me?.avatar_url ? apiUrl(me.avatar_url) : "";
  const statusLabel = (status: string) => (status === "approved" ? ar.bannerApproved : status === "rejected" ? ar.bannerRejected : ar.bannerPending);

  return (
    <RoleShell role="company_manager" title={ar.settings}>
      {company ? (
        <section className={`${cardClass} flex flex-col gap-4`}>
          <div className="flex items-center gap-3">
            <span className="relative h-16 w-16 shrink-0 overflow-hidden rounded-2xl bg-secondary text-on-secondary shadow-sm">
              {photo ? <img src={photo} alt="" className="h-full w-full object-cover" /> : <Icon name="manage_accounts" className="text-[32px]" />}
            </span>
            <div className="min-w-0">
              <h2 className="truncate text-lg font-extrabold">{me?.full_name}</h2>
              <p className="text-sm text-secondary">{ar.managerAccount}</p>
              <p className="truncate text-sm font-bold text-primary">{company.name}</p>
            </div>
          </div>
          <div className="grid gap-2 sm:grid-cols-2">
            <div className="rounded-2xl bg-surface-low p-2.5">
              <span className="block text-xs text-secondary">{ar.phone}</span>
              <span dir="ltr" className="font-bold">{company.phone}</span>
            </div>
            <div className="rounded-2xl bg-surface-low p-2.5">
              <div className="flex items-center justify-between gap-2">
                <span>
                  <span className="block text-xs text-secondary">{ar.companyBalance}</span>
                  <span className="font-bold">{company.balance} {ar.currency}</span>
                </span>
                <button type="button" className="rounded-xl bg-primary-container px-3 py-2 text-xs font-bold text-white transition hover:opacity-90" onClick={() => setTopUp((open) => !open)}>
                  {ar.creditBalance}
                </button>
              </div>
            </div>
          </div>
          <p className="text-xs text-secondary">{ar.balanceFundsAds}</p>
          {topUp ? (
            <form className="flex gap-2" onSubmit={addBalance}>
              <input name="amount" required type="number" min="0.01" step="0.01" placeholder={ar.creditBalance} className={fieldClass} />
              <button className={`${primaryButton} shrink-0 transition hover:opacity-90`} type="submit">{ar.creditBalance}</button>
            </form>
          ) : null}
        </section>
      ) : null}

      {notice ? <Notice>{notice}</Notice> : null}

      <section className="flex flex-col gap-2">
        <h3 className="flex items-center gap-2 px-1 font-extrabold"><span className="h-4 w-2 rounded-full bg-primary-container" />{ar.companySection}</h3>
        <div className={`${cardClass} flex flex-col gap-1`}>
          <button type="button" className={rowClass} onClick={() => toggle("company")}>
            <span className="flex items-center gap-3">
              <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-surface-container text-secondary"><Icon name="corporate_fare" className="text-[22px]" /></span>
              <span>
                <span className="block font-extrabold">{ar.companyRecord}</span>
                <span className="text-sm text-secondary">{company?.name}</span>
              </span>
            </span>
            <Icon name="chevron_left" className="text-secondary" />
          </button>
          {panel === "company" && company ? (
            <form className="mx-3 mb-3 grid gap-2 rounded-2xl bg-surface-low p-3" onSubmit={saveCompany}>
              <input name="name" required defaultValue={company.name} placeholder={ar.companyName} className={fieldClass} />
              <textarea name="description" defaultValue={company.description} placeholder={ar.description} className={fieldClass} rows={3} />
              <input name="phone" required defaultValue={company.phone} placeholder={ar.phone} className={fieldClass} />
              <input name="monthly_sales_target" required type="number" min="0" step="0.01" defaultValue={report?.monthly_target ?? "0"} placeholder={ar.salesTarget} className={fieldClass} />
              <button className={`${primaryButton} w-fit transition hover:opacity-90`} type="submit">{ar.save}</button>
            </form>
          ) : null}
          <Link href="/company/towers" className={rowClass}>
            <span className="flex items-center gap-3">
              <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-primary-fixed/50 text-primary"><Icon name="cell_tower" className="text-[22px]" /></span>
              <span>
                <span className="block font-extrabold">{ar.towers}</span>
                <span className="text-sm text-secondary">{ar.coverage}</span>
              </span>
            </span>
            <Icon name="chevron_left" className="text-secondary" />
          </Link>
          <button type="button" className={rowClass} onClick={() => toggle("banners")}>
            <span className="flex items-center gap-3">
              <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-primary/10 text-primary"><Icon name="campaign" className="text-[22px]" /></span>
              <span className="font-extrabold">{ar.banners}</span>
            </span>
            <Icon name="chevron_left" className="text-secondary" />
          </button>
          {panel === "banners" ? (
            <div className="flex flex-col gap-3 px-3 pb-3">
              <p className="rounded-2xl bg-surface-low p-3 text-sm font-bold">{ar.bannerCost}: {price} {ar.currency}</p>
              <form className="grid gap-2" onSubmit={createBanner}>
                <input name="title" required placeholder={ar.adTitle} className={fieldClass} />
                <textarea name="body" placeholder={ar.adBody} className={fieldClass} rows={2} />
                <input name="image" type="file" accept="image/png,image/jpeg,image/webp" className={`${fieldClass} py-3`} />
                <button className={`${primaryButton} w-fit transition hover:opacity-90`} type="submit">{ar.submitBanner}</button>
              </form>
              {banners.map((banner) => (
                <p key={banner.id} className="rounded-2xl bg-surface-low px-3 py-2 text-sm">
                  <span className="font-extrabold">{banner.title}</span> — {statusLabel(banner.status)} — {banner.price} {ar.currency}
                </p>
              ))}
            </div>
          ) : null}
        </div>
      </section>

      <section className="flex flex-col gap-2">
        <h3 className="flex items-center gap-2 px-1 font-extrabold"><span className="h-4 w-2 rounded-full bg-secondary" />{ar.securitySection}</h3>
        <div className={cardClass}>
          <InlineAccount />
        </div>
      </section>

      <section className="flex flex-col gap-2">
        <h3 className="flex items-center gap-2 px-1 font-extrabold"><span className="h-4 w-2 rounded-full bg-secondary" />{ar.complaints}</h3>
        <div className={`${cardClass} flex flex-col gap-1`}>
          <button type="button" className={rowClass} onClick={() => toggle("support")}>
            <span className="flex items-center gap-3">
              <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-primary-fixed/50 text-primary"><Icon name="support_agent" className="text-[22px]" /></span>
              <span>
                <span className="block font-extrabold">{ar.platformSupport}</span>
                <span className="text-sm text-secondary">{ar.supportHint}</span>
              </span>
            </span>
            <Icon name="chevron_left" className="text-secondary" />
          </button>
          {panel === "support" ? (
            <div className="flex flex-col gap-2 px-3 pb-3">
              <form className="flex flex-col gap-2" onSubmit={sendSupport}>
                <textarea name="message" required rows={3} placeholder={ar.reply} className={fieldClass} />
                <button className={`${primaryButton} w-fit transition hover:opacity-90`} type="submit">{ar.send}</button>
              </form>
              {messages.map((row) => (
                <article key={row.id} className="rounded-2xl bg-surface-low p-3 text-sm">
                  <p>{row.message}</p>
                  {row.reply_message ? <p className="mt-2 font-bold text-tertiary">{row.reply_message}</p> : <p className="mt-2 text-secondary">{ar.noReply}</p>}
                </article>
              ))}
            </div>
          ) : null}
          <Link href="/company/complaints" className={rowClass}>
            <span className="flex items-center gap-3">
              <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-surface-container text-secondary"><Icon name="confirmation_number" className="text-[22px]" /></span>
              <span className="font-extrabold">{ar.subscriberTickets}</span>
            </span>
            <Icon name="chevron_left" className="text-secondary" />
          </Link>
        </div>
      </section>

      {ledger.length > 0 ? (
        <section className={`${cardClass} flex flex-col gap-2`}>
          <h3 className="font-extrabold">{ar.ledger}</h3>
          {ledger.slice(0, 6).map((row) => (
            <p key={row.id} className="flex items-center justify-between rounded-2xl bg-surface-low px-3 py-2 text-sm">
              <span>{row.note}</span>
              <span className="font-bold" dir="ltr">{row.kind === "banner_expense" ? "-" : "+"}{row.amount}</span>
            </p>
          ))}
        </section>
      ) : null}

      <button type="button" onClick={logout} className="flex h-14 w-full items-center justify-center gap-2 rounded-2xl bg-error-container font-extrabold text-error transition hover:opacity-90">
        <Icon name="logout" className="text-[22px]" />
        {ar.logoutManager}
      </button>
    </RoleShell>
  );
}
