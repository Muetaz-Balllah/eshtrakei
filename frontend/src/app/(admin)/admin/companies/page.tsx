"use client";

import { FormEvent, useEffect, useState } from "react";
import { RoleShell } from "@/components/shell/role-shell";
import { cardClass, fieldClass, ghostButton, Icon, Notice, primaryButton } from "@/components/ui/ui";
import { apiFetch, apiUrl, authHeaders } from "@/lib/api";
import { passwordIsStrong } from "@/lib/password";
import { ar } from "@/messages/ar";

type Company = { id: number; name: string; description: string; status: string; phone: string; has_manager: boolean };
type RequestRow = { id: number; name: string; description: string; phone: string; status: string; created_at: string };
type Performance = {
  total_gross_sales: string;
  total_platform_net_revenue: string;
  total_active_companies: number;
  total_registered_clients: number;
  total_active_subscriptions: number;
  pending_join_requests: number;
  stopped_companies: number;
  revenue_change_percent: number | null;
};

const statusLabel: Record<string, string> = {
  pending: ar.pending,
  approved: ar.approved,
  rejected: ar.rejected,
  stopped: ar.stopped,
};

export default function AdminCompaniesPage() {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [requests, setRequests] = useState<RequestRow[]>([]);
  const [stats, setStats] = useState<Performance | null>(null);
  const [notice, setNotice] = useState("");
  const [showAll, setShowAll] = useState(false);

  async function reload() {
    const headers = authHeaders();
    const [companyResponse, requestResponse, statsResponse] = await Promise.all([
      fetch(apiUrl("/api/admin/companies"), { headers }),
      fetch(apiUrl("/api/admin/join-requests"), { headers }),
      apiFetch("/api/admin/performance", { headers }),
    ]);
    if (companyResponse.ok) setCompanies(await companyResponse.json());
    if (requestResponse.ok) setRequests(await requestResponse.json());
    if (statsResponse.ok) setStats(await statsResponse.json());
  }

  useEffect(() => {
    reload();
  }, []);

  async function decide(id: number, action: "approve" | "reject") {
    await fetch(apiUrl(`/api/admin/join-requests/${id}/${action}`), { method: "POST", headers: authHeaders() });
    await reload();
  }

  async function stop(id: number) {
    await fetch(apiUrl(`/api/admin/companies/${id}/stop`), { method: "POST", headers: authHeaders() });
    await reload();
  }

  async function resume(id: number) {
    await fetch(apiUrl(`/api/admin/companies/${id}/resume`), { method: "POST", headers: authHeaders() });
    await reload();
  }

  async function createManager(event: FormEvent<HTMLFormElement>, companyId: number) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    if (String(form.get("password") ?? "") !== String(form.get("confirm_password") ?? "")) {
      setNotice(ar.passwordMismatch);
      return;
    }
    if (!passwordIsStrong(String(form.get("password") ?? ""))) {
      setNotice(ar.passwordHint);
      return;
    }
    const response = await fetch(apiUrl(`/api/admin/companies/${companyId}/manager`), {
      method: "POST",
      headers: { ...authHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({
        full_name: form.get("full_name"),
        email: form.get("email"),
        password: form.get("password"),
      }),
    });
    const body = await response.json().catch(() => ({}));
    setNotice(response.ok ? ar.managerCreated : body.message ?? ar.passwordHint);
    await reload();
  }

  const pending = requests.filter((row) => row.status === "pending");
  const stopped = companies.filter((company) => company.status === "stopped");
  const queueCount = pending.length + stopped.length;
  const change = stats?.revenue_change_percent;

  return (
    <RoleShell role="platform_admin" title={ar.overview}>
      <section className={`${cardClass} relative overflow-hidden`}>
        <div className="pointer-events-none absolute -start-12 -top-12 h-40 w-40 rounded-full bg-secondary-fixed/40 blur-3xl" />
        <div className="pointer-events-none absolute -end-10 -bottom-10 h-36 w-36 rounded-full bg-primary-container/20 blur-2xl" />
        <div className="relative flex items-start justify-between gap-3">
          <div className="flex flex-col gap-2">
            <div className="flex items-center gap-2">
              <span className="rounded-full bg-secondary-fixed px-2.5 py-1 text-xs font-bold text-on-secondary-fixed">{ar.platformSupervisor}</span>
              <span className="h-1.5 w-1.5 rounded-full bg-tertiary-container" />
            </div>
            <h2 className="text-xl font-extrabold">{ar.infraTitle}</h2>
          </div>
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-surface-container text-secondary shadow-sm">
            <Icon name="admin_panel_settings" className="text-[22px]" />
          </span>
        </div>
      </section>

      {stats ? (
        <section className="flex flex-col gap-3">
          <article className="relative overflow-hidden rounded-3xl bg-primary-container p-5 text-white shadow-[0_10px_25px_-5px_rgba(245,130,32,0.35)]">
            <div className="pointer-events-none absolute -end-8 -top-8 h-32 w-32 rounded-full bg-white/10 blur-xl" />
            <div className="relative flex flex-col gap-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-white/20">
                    <Icon name="account_balance_wallet" className="text-[20px]" />
                  </span>
                  <span className="font-bold">{ar.platformRevenueTotal}</span>
                </div>
                {change !== null && change !== undefined ? (
                  <span className="inline-flex items-center gap-1 rounded-full bg-white px-2.5 py-1 text-xs font-bold text-primary">
                    <Icon name={change >= 0 ? "trending_up" : "trending_down"} className="text-[14px]" />
                    {change > 0 ? "+" : ""}{change}% {ar.thisMonth}
                  </span>
                ) : null}
              </div>
              <div className="flex flex-wrap items-end justify-between gap-2">
                <p className="text-3xl font-extrabold tracking-tight">
                  {stats.total_platform_net_revenue} <span className="text-base font-bold text-white/90">{ar.currency}</span>
                </p>
                <p className="text-sm text-white/80">{ar.grossSales}: {stats.total_gross_sales} {ar.currency}</p>
              </div>
            </div>
          </article>
          <div className="grid grid-cols-2 gap-3">
            <article className={`${cardClass} flex flex-col justify-between`}>
              <div className="mb-2 flex items-center justify-between">
                <span className="text-sm font-bold text-secondary">{ar.providers}</span>
                <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-secondary-fixed text-on-secondary-fixed">
                  <Icon name="hub" className="text-[18px]" />
                </span>
              </div>
              <p className="text-3xl font-extrabold">{stats.total_active_companies} <span className="text-xs font-bold text-secondary">{ar.companies}</span></p>
              <p className="mt-1 flex items-center gap-1.5 text-xs text-secondary">
                <span className="h-2 w-2 rounded-full bg-tertiary-container" />
                {stats.total_active_companies} {ar.active} • {stats.pending_join_requests} {ar.pending}
              </p>
            </article>
            <article className={`${cardClass} flex flex-col justify-between`}>
              <div className="mb-2 flex items-center justify-between">
                <span className="text-sm font-bold text-secondary">{ar.subscribers}</span>
                <span className="flex h-8 w-8 items-center justify-center rounded-xl bg-surface-container text-secondary">
                  <Icon name="group" className="text-[18px]" />
                </span>
              </div>
              <p className="text-3xl font-extrabold">{stats.total_registered_clients}</p>
              <p className="mt-1 text-xs text-secondary">{ar.activeSubscriptions}: {stats.total_active_subscriptions}</p>
            </article>
          </div>
        </section>
      ) : null}

      {queueCount > 0 ? (
        <a href="#requests" className="flex items-center justify-between rounded-3xl bg-primary-fixed px-5 py-4 font-extrabold text-primary">
          <span>{queueCount} {ar.joinQueue}</span>
          <Icon name="chevron_left" />
        </a>
      ) : null}

      {notice ? <Notice>{notice}</Notice> : null}

      <section id="requests" className="flex flex-col gap-3">
        <div className="flex items-center justify-between px-1">
          <div className="flex items-center gap-2">
            <Icon name="pending_actions" className="text-secondary text-[22px]" />
            <h2 className="text-lg font-extrabold">{ar.joinQueue}</h2>
          </div>
          <span className="rounded-full bg-primary-fixed px-2.5 py-0.5 text-xs font-bold text-primary">{queueCount}</span>
        </div>
        <div className="grid gap-3 xl:grid-cols-2">
          {pending.map((row) => (
            <article key={row.id} className={`${cardClass} flex flex-col gap-3`}>
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2.5">
                  <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-surface-container text-sm font-extrabold text-secondary">{row.name.slice(0, 1)}</span>
                  <h3 className="font-extrabold">{row.name}</h3>
                </div>
                <span className="shrink-0 rounded-full bg-primary-fixed px-2.5 py-1 text-xs font-bold text-primary">{ar.pending}</span>
              </div>
              <div className="flex flex-col gap-1 rounded-2xl bg-surface-low p-3 text-sm text-secondary">
                <div className="flex items-center justify-between gap-3">
                  <span>{ar.description}</span>
                  <span className="text-end font-bold text-on-surface">{row.description || "—"}</span>
                </div>
                <div className="flex items-center justify-between gap-3">
                  <span>{ar.phone}</span>
                  <span dir="ltr" className="font-bold text-secondary">{row.phone}</span>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button type="button" className="inline-flex h-11 flex-1 items-center justify-center gap-1.5 rounded-2xl bg-secondary text-sm font-bold text-on-secondary" onClick={() => decide(row.id, "approve")}>
                  <Icon name="check_circle" className="text-[18px]" />
                  {ar.approveActivate}
                </button>
                <button type="button" aria-label={ar.reject} className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-error-container text-error" onClick={() => decide(row.id, "reject")}>
                  <Icon name="close" className="text-[20px]" />
                </button>
              </div>
            </article>
          ))}
          {stopped.map((company) => (
            <article key={company.id} className={`${cardClass} flex flex-col gap-3`}>
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2.5">
                  <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-error-container text-sm font-extrabold text-error">{company.name.slice(0, 1)}</span>
                  <h3 className="font-extrabold">{company.name}</h3>
                </div>
                <span className="shrink-0 rounded-full bg-error-container px-2.5 py-1 text-xs font-bold text-error">{ar.stopped}</span>
              </div>
              <div className="flex flex-col gap-1 rounded-2xl bg-surface-low p-3 text-sm text-secondary">
                <div className="flex items-center justify-between gap-3">
                  <span>{ar.description}</span>
                  <span className="text-end font-bold text-on-surface">{company.description || "—"}</span>
                </div>
                <div className="flex items-center justify-between gap-3">
                  <span>{ar.phone}</span>
                  <span dir="ltr" className="font-bold text-secondary">{company.phone}</span>
                </div>
              </div>
              <button type="button" className={`${primaryButton} w-full`} onClick={() => resume(company.id)}>
                <Icon name="lock_open" className="text-[18px]" />
                {ar.resumeCompany}
              </button>
            </article>
          ))}
        </div>
        <button type="button" className={`${cardClass} flex h-14 w-full items-center justify-center gap-2 font-bold text-secondary`} onClick={() => setShowAll((value) => !value)}>
          <span>{ar.showAllCompanies} ({companies.length})</span>
          <Icon name="arrow_forward" className="text-[20px] rtl:-scale-x-100" />
        </button>
      </section>

      {showAll ? (
        <section className="grid gap-4 xl:grid-cols-2">
          {companies.map((company) => (
            <article key={company.id} className={`${cardClass} flex flex-col gap-4`}>
              <div className="flex flex-wrap items-center justify-between gap-2">
                <h3 className="text-lg font-extrabold">{company.name}</h3>
                <span className="rounded-full bg-surface-container px-2.5 py-1 text-xs font-bold text-secondary">{statusLabel[company.status] ?? company.status}</span>
              </div>
              <p className="text-sm text-secondary">{company.description}</p>
              <p dir="ltr" className="rounded-2xl bg-surface-low px-3 py-2 text-sm font-semibold text-secondary">{company.phone}</p>
              {company.status === "approved" ? (
                <button type="button" className={`${ghostButton} w-fit`} onClick={() => stop(company.id)}>{ar.stopCompany}</button>
              ) : null}
              {company.status === "stopped" ? (
                <button type="button" className={`${primaryButton} w-fit`} onClick={() => resume(company.id)}>{ar.resumeCompany}</button>
              ) : null}
              {company.status === "approved" && !company.has_manager ? (
                <form className="grid gap-2 md:grid-cols-2" onSubmit={(event) => createManager(event, company.id)}>
                  <input name="full_name" required placeholder={ar.fullName} className={fieldClass} />
                  <input name="email" required type="email" placeholder={ar.email} className={fieldClass} />
                  <input name="password" required minLength={8} type="password" placeholder={ar.passwordHint} className={fieldClass} />
                  <input name="confirm_password" required type="password" placeholder={ar.confirmPassword} className={fieldClass} />
                  <button type="submit" className={primaryButton}>{ar.createManager}</button>
                </form>
              ) : null}
            </article>
          ))}
        </section>
      ) : null}
    </RoleShell>
  );
}
