"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { RoleShell } from "@/components/shell/role-shell";
import { cardClass, Icon } from "@/components/ui/ui";
import { apiFetch, apiUrl, authHeaders } from "@/lib/api";
import { ar } from "@/messages/ar";

type Company = { name: string; description: string; phone: string; balance?: string };
type Me = { full_name: string; avatar_url: string | null };
type Point = { label: string; total: string };
type Report = {
  monthly_sales: Point[];
  weekly_sales: Point[];
  yearly_sales: Point[];
  target_progress: number;
  current_month_revenue: string;
  current_month_net: string;
  commission_percentage: number;
  revenue_change_percent: number | null;
  active_subscribers: number;
  new_subscribers_this_month: number;
  month_sales_count: number;
  sales_count_change_percent: number | null;
  average_ticket: string;
  renewal_rate: number | null;
  currency: string;
};
type Package = {
  id: number;
  name: string;
  price: string;
  data_gb: number;
  speed_mbps: number;
  download_mbps?: number;
  upload_mbps?: number;
  is_available: boolean;
  active_subscribers: number;
};
type Coupon = { id: number; code: string; discount_amount: string; max_uses: number | null; max_total_uses: number | null; redemption_count: number; expires_at: string };
type Sub = { id: number; package_name: string; status: string; start_date: string; days_remaining: number };
type ClientRow = { full_name: string; subscriptions: Sub[] };

const periods = [
  { id: "weekly", label: ar.weekly },
  { id: "monthly", label: ar.monthly },
  { id: "yearly", label: ar.yearly },
] as const;

const packageIcons = ["rocket_launch", "stream", "wifi"];

function initials(name: string) {
  return name.trim().split(/\s+/).slice(0, 2).map((part) => part[0]).join(".");
}

export default function CompanyHomePage() {
  const [company, setCompany] = useState<Company | null>(null);
  const [me, setMe] = useState<Me | null>(null);
  const [report, setReport] = useState<Report | null>(null);
  const [packages, setPackages] = useState<Package[]>([]);
  const [coupons, setCoupons] = useState<Coupon[]>([]);
  const [clients, setClients] = useState<ClientRow[]>([]);
  const [period, setPeriod] = useState<(typeof periods)[number]["id"]>("monthly");
  const [insight, setInsight] = useState<number | null>(null);

  useEffect(() => {
    const headers = authHeaders();
    Promise.all([
      apiFetch("/api/company/me", { headers }),
      apiFetch("/api/auth/me", { headers }),
      apiFetch("/api/company/reports/sales", { headers }),
      apiFetch("/api/company/packages", { headers }),
      apiFetch("/api/company/coupons", { headers }),
      apiFetch("/api/company/clients", { headers }),
    ]).then(async ([companyResponse, meResponse, reportResponse, packageResponse, couponResponse, clientResponse]) => {
      if (companyResponse.ok) setCompany(await companyResponse.json());
      if (meResponse.ok) setMe(await meResponse.json());
      if (reportResponse.ok) setReport(await reportResponse.json());
      if (packageResponse.ok) setPackages(await packageResponse.json());
      if (couponResponse.ok) setCoupons(await couponResponse.json());
      if (clientResponse.ok) setClients(await clientResponse.json());
    });
  }, []);

  async function pause(id: number) {
    await apiFetch(`/api/company/packages/${id}/stop`, { method: "POST", headers: authHeaders() });
    const response = await apiFetch("/api/company/packages", { headers: authHeaders() });
    if (response.ok) setPackages(await response.json());
  }

  async function resume(id: number) {
    await apiFetch(`/api/company/packages/${id}/resume`, { method: "POST", headers: authHeaders() });
    const response = await apiFetch("/api/company/packages", { headers: authHeaders() });
    if (response.ok) setPackages(await response.json());
  }

  async function removeCoupon(id: number) {
    await apiFetch(`/api/company/coupons/${id}`, { method: "DELETE", headers: authHeaders() });
    const response = await apiFetch("/api/company/coupons", { headers: authHeaders() });
    if (response.ok) setCoupons(await response.json());
  }

  const series = report ? (period === "weekly" ? report.weekly_sales ?? [] : period === "yearly" ? report.yearly_sales ?? [] : report.monthly_sales ?? []) : [];
  const max = Math.max(...series.map((point) => Number(point.total) || 0), 1);
  const current = series.at(-1);
  const popular = packages.reduce((best, row) => (row.active_subscribers > (best?.active_subscribers ?? 0) ? row : best), packages[0]);
  const recent = clients
    .flatMap((client) => client.subscriptions.map((sub) => ({ ...sub, full_name: client.full_name })))
    .sort((left, right) => right.start_date.localeCompare(left.start_date))
    .slice(0, 4);
  const change = report?.revenue_change_percent;

  return (
    <RoleShell role="company_manager" title={ar.managerDashboard}>
      {company ? (
        <section className={`${cardClass} relative overflow-hidden`}>
          <div className="pointer-events-none absolute -start-12 -top-12 h-40 w-40 rounded-full bg-primary-fixed/30 blur-2xl" />
          <div className="relative flex flex-col gap-4">
            <div className="flex items-center justify-between gap-2">
              <span className="inline-flex items-center gap-1.5 rounded-full bg-surface-low px-3 py-1 text-sm font-bold">
                <span className="flex h-5 w-5 items-center justify-center rounded-full bg-primary-container text-white">
                  <Icon name="bolt" className="text-[13px]" />
                </span>
                {company.name}
              </span>
              <span className="inline-flex items-center gap-1.5 rounded-full bg-tertiary/15 px-2.5 py-1 text-xs font-bold text-tertiary">
                <span className="h-2 w-2 rounded-full bg-tertiary" />
                {ar.active}
              </span>
            </div>
            <div className="flex items-center justify-between gap-3">
              <div className="flex min-w-0 items-center gap-3">
                <span className="relative flex h-14 w-14 shrink-0 items-center justify-center overflow-hidden rounded-2xl bg-secondary text-on-secondary shadow-md">
                  {me?.avatar_url ? <img src={apiUrl(me.avatar_url)} alt="" className="h-full w-full object-cover" /> : <Icon name="manage_accounts" className="text-[30px]" />}
                  <span className="absolute -bottom-1 -start-1 h-3.5 w-3.5 rounded-full bg-tertiary-container ring-2 ring-surface-lowest" />
                </span>
                <div className="min-w-0">
                  <h2 className="truncate text-lg font-extrabold">{me?.full_name}</h2>
                  <p className="text-sm text-secondary">{ar.managerAccount}</p>
                </div>
              </div>
              <div className="text-end">
                <p className="text-xs text-secondary">{ar.salesTarget}</p>
                <p className="text-2xl font-extrabold text-primary-container">{report?.target_progress ?? 0}%</p>
              </div>
            </div>
          </div>
        </section>
      ) : null}

      {report ? (
        <section className="flex flex-col gap-3">
          <h3 className="px-1 text-lg font-extrabold">{ar.financialKpis}</h3>
          <article className="relative overflow-hidden rounded-3xl bg-secondary p-5 text-on-secondary shadow-[0_12px_28px_rgba(30,58,95,0.15)]">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-sm text-secondary-fixed">{ar.netShare}</p>
                <p className="mt-1 text-3xl font-extrabold tracking-tight">
                  {report.current_month_net ?? report.current_month_revenue} <span className="text-lg text-primary-fixed">{report.currency}</span>
                </p>
                <p className="mt-1 text-xs text-secondary-fixed">{ar.afterCommission} {report.commission_percentage}%</p>
              </div>
              <span className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-primary-container text-white">
                <Icon name="account_balance_wallet" />
              </span>
            </div>
            <div className="mt-4 flex items-center justify-between rounded-2xl bg-white/10 px-3 py-3">
              <span className="text-sm text-secondary-fixed">{ar.grossBeforeFee}</span>
              <span className="text-lg font-extrabold">{report.current_month_revenue} <span className="text-sm text-primary-fixed">{report.currency}</span></span>
            </div>
            <div className="mt-3 flex items-center justify-between rounded-b-2xl bg-white/10 px-1 py-2 text-sm">
              {change !== null && change !== undefined ? (
                <span className="inline-flex items-center gap-1 font-bold text-primary-fixed">
                  <Icon name={change >= 0 ? "trending_up" : "trending_down"} className="text-[16px]" />
                  {change > 0 ? "+" : ""}{change}% {ar.growthVsLast}
                </span>
              ) : <span />}
              <span className="text-xs text-secondary-fixed">{current?.label}</span>
            </div>
          </article>
          <div className="grid grid-cols-2 gap-3">
            <article className={cardClass}>
              <div className="flex items-center justify-between">
                <span className="text-sm text-secondary">{ar.activeSubscriptions}</span>
                <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-surface-container text-secondary"><Icon name="group" className="text-[18px]" /></span>
              </div>
              <p className="mt-3 text-3xl font-extrabold">{report.active_subscribers} <span className="text-xs text-secondary">{ar.subscriberCount}</span></p>
              <span className="mt-2 inline-flex items-center gap-1 rounded-full bg-secondary-fixed/50 px-2 py-0.5 text-xs font-bold text-on-secondary-fixed">
                <Icon name="add" className="text-[12px]" />
                {report.new_subscribers_this_month} {ar.newThisMonth}
              </span>
            </article>
            <article className={cardClass}>
              <div className="flex items-center justify-between">
                <span className="text-sm text-secondary">{ar.packageSalesCount}</span>
                <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-surface-container text-primary-container"><Icon name="receipt_long" className="text-[18px]" /></span>
              </div>
              <p className="mt-3 text-3xl font-extrabold">{report.month_sales_count}</p>
              {report.sales_count_change_percent !== null ? (
                <span className="mt-2 inline-flex items-center gap-1 rounded-full bg-tertiary/15 px-2 py-0.5 text-xs font-bold text-tertiary">
                  <Icon name="speed" className="text-[12px]" />
                  {report.sales_count_change_percent > 0 ? "+" : ""}{report.sales_count_change_percent}%
                </span>
              ) : null}
            </article>
          </div>
        </section>
      ) : null}

      {report ? (
        <section className={`${cardClass} flex flex-col gap-4`}>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h3 className="text-lg font-extrabold">{ar.salesAnalytics}</h3>
              <p className="text-sm text-secondary">{ar.revenueTrend}</p>
            </div>
            <div className="flex rounded-full bg-surface-low p-1">
              {periods.map((item) => (
                <button key={item.id} type="button" onClick={() => setPeriod(item.id)} className={`rounded-full px-2.5 py-1 text-xs font-bold ${period === item.id ? "bg-secondary text-on-secondary shadow-sm" : "text-secondary"}`}>
                  {item.label}
                </button>
              ))}
            </div>
          </div>
          {current ? (
            <span className="inline-flex w-fit items-center gap-1 rounded-xl bg-secondary px-3 py-1 text-xs font-bold text-on-secondary">
              <span className="h-1.5 w-1.5 rounded-full bg-primary-container" />
              {current.label}: {current.total} {report.currency}
            </span>
          ) : null}
          <div className="flex h-44 items-end gap-3 px-1">
            {series.map((point, index) => {
              const value = Number(point.total) || 0;
              const height = Math.max(8, Math.round((value / max) * 128));
              const peak = index === series.length - 1;
              return (
                <div key={`${point.label}-${index}`} className="flex h-full flex-1 flex-col items-center justify-end gap-2">
                  <span className={`text-[11px] font-bold ${peak ? "text-primary-container" : "text-secondary"}`} dir="ltr">{point.total}</span>
                  <div className={`w-full rounded-t-xl ${peak ? "bg-primary-container shadow-[0_4px_12px_rgba(245,130,32,0.35)]" : "bg-surface-container"}`} style={{ height: `${height}px` }} />
                  <span className={`text-[11px] font-bold ${peak ? "text-primary" : "text-secondary"}`}>{point.label}</span>
                </div>
              );
            })}
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="flex items-center gap-2.5 rounded-2xl bg-surface-low p-3">
              <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-surface-lowest text-secondary shadow-sm"><Icon name="equalizer" className="text-[20px]" /></span>
              <span>
                <span className="block text-xs text-secondary">{ar.avgSubscription}</span>
                <span className="font-extrabold">{report.average_ticket} {report.currency}</span>
              </span>
            </div>
            <div className="flex items-center gap-2.5 rounded-2xl bg-surface-low p-3">
              <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-surface-lowest text-tertiary shadow-sm"><Icon name="autorenew" className="text-[20px]" /></span>
              <span>
                <span className="block text-xs text-secondary">{ar.renewalRate}</span>
                <span className="font-extrabold text-tertiary">{report.renewal_rate ?? 0}%</span>
              </span>
            </div>
          </div>
        </section>
      ) : null}

      <section className="flex flex-col gap-3">
        <div className="flex items-center justify-between gap-3 px-1">
          <div>
            <h3 className="text-lg font-extrabold">{ar.currentPackages}</h3>
            <p className="text-sm text-secondary">{ar.packageHint}</p>
          </div>
          <Link href="/company/packages" className="inline-flex h-10 items-center gap-1.5 rounded-full bg-primary-container px-3.5 text-sm font-bold text-white shadow-[0_4px_14px_rgba(245,130,32,0.3)]">
            <Icon name="add_circle" className="text-[18px]" />
            {ar.addPackage}
          </Link>
        </div>
        <div className="grid gap-3 xl:grid-cols-2">
          {packages.map((row, index) => (
            <article key={row.id} className={`${cardClass} flex flex-col gap-3 ${row.is_available ? "" : "opacity-70"}`}>
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-3">
                  <span className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl text-white shadow-sm ${index % 3 === 1 ? "bg-primary-container" : "bg-secondary"}`}>
                    <Icon name={packageIcons[index % packageIcons.length]} />
                  </span>
                  <div>
                    <div className="flex flex-wrap items-center gap-2">
                      <h4 className="font-extrabold">{row.name}</h4>
                      {popular?.id === row.id && row.active_subscribers > 0 ? (
                        <span className="rounded-full bg-tertiary/15 px-2 py-0.5 text-xs font-bold text-tertiary">{ar.mostRequested}</span>
                      ) : null}
                    </div>
                    <p className="text-sm text-secondary">{row.is_available ? ar.available : ar.hidden}</p>
                  </div>
                </div>
                <div className="text-end">
                  <p className="font-extrabold text-primary-container">{row.price} <span className="text-xs text-secondary">{ar.perMonth}</span></p>
                  <p className="text-xs text-secondary">{row.active_subscribers} {ar.subscriberCount}</p>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-2 rounded-2xl bg-surface-low p-2.5 text-sm font-bold">
                <span className="inline-flex items-center gap-2"><Icon name="speed" className="text-secondary text-[18px]" />{row.download_mbps || row.speed_mbps}/{row.upload_mbps || row.speed_mbps}</span>
                <span className="inline-flex items-center gap-2"><Icon name="data_usage" className="text-primary-container text-[18px]" />{row.data_gb} GB</span>
              </div>
              {insight === row.id ? <p className="text-sm font-bold text-secondary">{ar.consumptionStats}: {row.active_subscribers}</p> : null}
              <div className="flex items-center justify-between">
                <button type="button" className="inline-flex items-center gap-1 text-xs font-bold text-secondary" onClick={() => setInsight(insight === row.id ? null : row.id)}>
                  <Icon name="insights" className="text-[18px]" />
                  {ar.consumptionStats}
                </button>
                <div className="flex gap-2">
                  <Link href="/company/packages" aria-label={ar.save} className="flex h-9 w-9 items-center justify-center rounded-xl bg-surface-low text-secondary">
                    <Icon name="edit" className="text-[18px]" />
                  </Link>
                  {row.is_available ? (
                    <button type="button" aria-label={ar.hidePackage} className="flex h-9 w-9 items-center justify-center rounded-xl bg-error-container text-error" onClick={() => pause(row.id)}>
                      <Icon name="pause_circle" className="text-[18px]" />
                    </button>
                  ) : (
                    <button type="button" aria-label={ar.resumePackage} className="flex h-9 w-9 items-center justify-center rounded-xl bg-tertiary/15 text-tertiary" onClick={() => resume(row.id)}>
                      <Icon name="play_circle" className="text-[18px]" />
                    </button>
                  )}
                </div>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className={`${cardClass} flex flex-col gap-3`}>
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2.5">
            <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-primary-fixed text-primary"><Icon name="confirmation_number" className="text-[20px]" /></span>
            <div>
              <h3 className="font-extrabold">{ar.promoCodes}</h3>
              <p className="text-sm text-secondary">{ar.promoHint}</p>
            </div>
          </div>
          <Link href="/company/coupons" className="text-sm font-bold text-primary">+ {ar.newCode}</Link>
        </div>
        {coupons.slice(0, 3).map((coupon) => {
          const limit = coupon.max_total_uses ?? coupon.max_uses;
          const width = limit ? Math.min(100, Math.round((coupon.redemption_count / limit) * 100)) : 0;
          return (
            <div key={coupon.id} className="flex flex-col gap-2 rounded-2xl bg-surface-low p-3.5">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span dir="ltr" className="rounded-lg bg-surface-lowest px-2.5 py-1 font-extrabold tracking-widest shadow-sm">{coupon.code}</span>
                  <span className="rounded-full bg-tertiary/15 px-2 py-0.5 text-xs font-bold text-tertiary">{coupon.discount_amount} {ar.currency}</span>
                </div>
                <button type="button" className="text-xs font-bold text-error" onClick={() => removeCoupon(coupon.id)}>{ar.remove}</button>
                <span className="inline-flex items-center gap-1 text-xs text-secondary">
                  <Icon name="timer" className="text-[14px]" />
                  {limit ? `${ar.remainingUses} ${Math.max(limit - coupon.redemption_count, 0)}` : `${ar.usedTimes}: ${coupon.redemption_count}`}
                </span>
              </div>
              {limit ? (
                <div className="h-1.5 overflow-hidden rounded-full bg-surface-container">
                  <div className="h-full rounded-full bg-primary-container" style={{ width: `${width}%` }} />
                </div>
              ) : null}
            </div>
          );
        })}
      </section>

      <section className={`${cardClass} flex flex-col gap-3`}>
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-extrabold">{ar.recentSubscribers}</h3>
            <p className="text-sm text-secondary">{ar.recentHint}</p>
          </div>
          <span className="flex h-8 w-8 items-center justify-center rounded-full bg-surface-low text-secondary"><Icon name="person_search" className="text-[18px]" /></span>
        </div>
        {recent.map((row) => {
          const renew = row.status === "expired" || row.days_remaining <= 0;
          return (
            <div key={row.id} className="flex items-center justify-between gap-3 rounded-2xl bg-surface-low p-3">
              <div className="flex min-w-0 items-center gap-3">
                <span className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl text-sm font-extrabold ${renew ? "bg-error-container text-error" : "bg-surface-container text-secondary"}`}>{initials(row.full_name)}</span>
                <div className="min-w-0">
                  <p className="truncate font-extrabold">{row.full_name}</p>
                  <p className="truncate text-sm text-secondary">{row.package_name} • {row.days_remaining} {ar.days}</p>
                </div>
              </div>
              <span className={`inline-flex shrink-0 items-center gap-1 rounded-full px-2.5 py-1 text-xs font-bold ${renew ? "bg-error-container text-error" : "bg-tertiary/15 text-tertiary"}`}>
                <span className={`h-1.5 w-1.5 rounded-full ${renew ? "bg-error" : "bg-tertiary"}`} />
                {renew ? ar.needsRenewal : ar.active}
              </span>
            </div>
          );
        })}
        <Link href="/company/clients" className="flex h-12 items-center justify-center gap-2 rounded-2xl bg-secondary font-bold text-on-secondary">
          {ar.viewAllSubscribers} ({report?.active_subscribers ?? clients.length})
          <Icon name="arrow_back" className="text-[18px]" />
        </Link>
      </section>
    </RoleShell>
  );
}
