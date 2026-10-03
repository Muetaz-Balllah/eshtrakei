"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import { InlineAccount } from "@/components/account/inline-account";
import { RoleShell, useLogout } from "@/components/shell/role-shell";
import { cardClass, fieldClass, Icon, Notice, primaryButton } from "@/components/ui/ui";
import { apiFetch, apiUrl, authHeaders } from "@/lib/api";
import { ar } from "@/messages/ar";

type Settings = {
  platform_commission_percentage: number;
  allow_company_registration: boolean;
  expiry_warning_days: number[];
  support_email: string;
  banner_price: number;
};
type Me = { full_name: string; phone: string | null; email: string; avatar_url: string | null };

export default function SettingsPage() {
  const [form, setForm] = useState<Settings | null>(null);
  const [me, setMe] = useState<Me | null>(null);
  const [saved, setSaved] = useState(false);
  const logout = useLogout();

  useEffect(() => {
    apiFetch("/api/admin/settings", { headers: authHeaders() })
      .then((response) => (response.ok ? response.json() : null))
      .then(setForm);
    apiFetch("/api/auth/me", { headers: authHeaders() })
      .then((response) => (response.ok ? response.json() : null))
      .then(setMe);
    function onProfile(event: Event) {
      const detail = (event as CustomEvent<Me>).detail;
      if (detail?.avatar_url !== undefined) setMe((current) => (current ? { ...current, ...detail } : current));
    }
    window.addEventListener("eshtrakei-profile", onProfile);
    return () => window.removeEventListener("eshtrakei-profile", onProfile);
  }, []);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!form) return;
    const response = await apiFetch("/api/admin/settings", {
      method: "PUT",
      headers: { ...authHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({ ...form, allow_company_registration: true }),
    });
    if (response.ok) {
      setForm(await response.json());
      setSaved(true);
    }
  }

  return (
    <RoleShell role="platform_admin" title={ar.settings}>
      <section className={`${cardClass} relative flex flex-col gap-4 overflow-hidden`}>
        <div className="pointer-events-none absolute -start-12 -top-12 h-32 w-32 rounded-full bg-primary/10 blur-2xl" />
        <div className="relative flex items-center gap-3">
          <span className="relative flex h-14 w-14 items-center justify-center overflow-hidden rounded-2xl bg-secondary text-on-secondary shadow-md">
            {me?.avatar_url ? <img src={apiUrl(me.avatar_url)} alt="" className="h-full w-full object-cover" /> : <Icon name="admin_panel_settings" className="text-[30px]" />}
            <span className="absolute -bottom-1 -start-1 flex h-4 w-4 items-center justify-center rounded-full bg-tertiary-container ring-2 ring-surface-lowest">
              <span className="h-1.5 w-1.5 rounded-full bg-surface-lowest" />
            </span>
          </span>
          <div>
            <div className="flex items-center gap-1.5">
              <h2 className="text-lg font-extrabold">{me?.full_name ?? ar.superAdmin}</h2>
              <Icon name="verified" className="text-primary text-[18px]" />
            </div>
            <p className="text-sm text-secondary">{ar.superAdmin}</p>
            <p className="text-xs text-secondary" dir="ltr">{me?.email}</p>
          </div>
        </div>
        {me?.phone ? (
          <span className="inline-flex w-fit items-center gap-1.5 rounded-full bg-secondary-fixed px-3 py-1 text-xs font-bold text-on-secondary-fixed">
            <Icon name="call" className="text-[14px]" />
            <span dir="ltr">{me.phone}</span>
          </span>
        ) : null}
      </section>

      <section className="flex flex-col gap-2.5">
        <div className="flex items-center justify-between px-1">
          <h2 className="font-bold text-secondary">{ar.policies}</h2>
        </div>
        {form ? (
          <form onSubmit={onSubmit} className={`${cardClass} flex flex-col gap-4`}>
            <div className="flex items-center gap-3 rounded-2xl bg-surface-low p-3">
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
                <Icon name="account_balance" className="text-[22px]" />
              </span>
              <span>
                <span className="block font-extrabold">{ar.commissionPolicies}</span>
                <span className="text-xs text-secondary">{form.platform_commission_percentage}%</span>
              </span>
            </div>
            <label className="flex flex-col gap-2 text-sm font-bold text-secondary">
              {ar.commission}
              <input type="number" min="0" max="100" step="0.1" className={fieldClass} value={form.platform_commission_percentage} onChange={(event) => setForm({ ...form, platform_commission_percentage: Number(event.target.value) })} />
            </label>
            <label className="flex flex-col gap-2 text-sm font-bold text-secondary">
              {ar.bannerPrice}
              <input type="number" min="0" step="0.01" className={fieldClass} value={form.banner_price ?? 0} onChange={(event) => setForm({ ...form, banner_price: Number(event.target.value) })} />
            </label>
            <label className="flex flex-col gap-2 text-sm font-bold text-secondary">
              {ar.supportEmail}
              <input type="email" className={fieldClass} value={form.support_email} onChange={(event) => setForm({ ...form, support_email: event.target.value })} />
            </label>
            <p className="rounded-2xl bg-surface-low px-4 py-3 text-sm font-bold">{ar.joinAlwaysReviewed}</p>
            <label className="flex flex-col gap-2 text-sm font-bold text-secondary">
              {ar.warningDays}
              <input className={fieldClass} value={form.expiry_warning_days.join(",")} onChange={(event) => setForm({ ...form, expiry_warning_days: event.target.value.split(",").map((part) => Number(part.trim())).filter((day) => day > 0) })} />
            </label>
            <button className={`${primaryButton} w-fit`} type="submit">{ar.saveSettings}</button>
            {saved ? <Notice>{ar.saveSettings}</Notice> : null}
          </form>
        ) : null}
      </section>

      <section className="flex flex-col gap-2.5">
        <h2 className="px-1 font-bold text-secondary">{ar.alertsSection}</h2>
        <div className={`${cardClass} flex flex-col gap-4`}>
          <Link href="/admin/banners" className="flex items-center justify-between gap-3 rounded-2xl bg-surface-low p-3">
            <span className="flex items-center gap-3">
              <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/10 text-primary"><Icon name="campaign" className="text-[22px]" /></span>
              <span>
                <span className="block font-extrabold">{ar.banners}</span>
                <span className="text-xs text-secondary">{ar.ads}</span>
              </span>
            </span>
            <Icon name="chevron_left" className="text-secondary" />
          </Link>
        </div>
      </section>

      <section className="flex flex-col gap-2.5">
        <h2 className="px-1 font-bold text-secondary">{ar.securityAccess}</h2>
        <InlineAccount />
      </section>

      <section className="flex flex-col items-center gap-3 pt-2">
        <button type="button" onClick={logout} className="flex h-14 w-full items-center justify-center gap-2 rounded-2xl bg-error font-bold text-white shadow-md">
          <Icon name="logout" className="text-[20px]" />
          {ar.logoutAdmin}
        </button>
        <p className="flex items-center gap-1.5 pb-2 text-center text-sm text-secondary">
          <span className="h-2 w-2 rounded-full bg-tertiary-container" />
          {ar.versionStamp}
        </p>
      </section>
    </RoleShell>
  );
}
