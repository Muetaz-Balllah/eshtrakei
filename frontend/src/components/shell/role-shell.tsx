"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { ThemeToggle } from "@/components/shell/theme-toggle";
import { Icon } from "@/components/ui/ui";
import { apiFetch, apiUrl, authHeaders } from "@/lib/api";
import { clearSession, getRole, getToken } from "@/lib/auth-storage";
import { ar } from "@/messages/ar";

type NavItem = { href: string; label: string; icon: string; match: string[] };

const navigation: Record<string, NavItem[]> = {
  client: [
    { href: "/client/companies", label: ar.clientHome, icon: "home", match: ["/client/companies"] },
    { href: "/client/store", label: ar.store, icon: "store", match: ["/client/store", "/client/checkout", "/packages"] },
    { href: "/client/settings", label: ar.settings, icon: "settings", match: ["/client/settings", "/client/complaints", "/client/subscriptions", "/client/wallet", "/client/invoices", "/client/coverage", "/client/notifications"] },
  ],
  platform_admin: [
    { href: "/admin/companies", label: ar.overview, icon: "home", match: ["/admin/companies", "/admin/performance", "/admin/join-requests"] },
    { href: "/admin/complaints", label: ar.complaints, icon: "confirmation_number", match: ["/admin/complaints"] },
    { href: "/admin/settings", label: ar.settings, icon: "settings", match: ["/admin/settings", "/admin/banners", "/admin/notifications"] },
  ],
  company_manager: [
    {
      href: "/company",
      label: ar.managerDashboard,
      icon: "dashboard",
      match: ["/company/packages", "/company/coupons", "/company/clients", "/company/reports"],
    },
    { href: "/company/settings", label: ar.settings, icon: "settings", match: ["/company/settings", "/company/complaints", "/company/towers", "/company/notifications"] },
  ],
};

const bellHref: Record<string, string> = {
  client: "/client/notifications",
  platform_admin: "/admin/notifications",
  company_manager: "/company/notifications",
};

const headerBadge: Record<string, string> = {
  platform_admin: `${ar.superAdmin} - Super Admin`,
  company_manager: ar.managerAccount,
};

function isActive(pathname: string, item: NavItem) {
  if (item.href === "/client/companies") return pathname === "/client/companies";
  if (item.href === "/company") return pathname === "/company" || item.match.some((prefix) => pathname.startsWith(prefix));
  return pathname === item.href || pathname.startsWith(`${item.href}/`) || item.match.some((prefix) => pathname.startsWith(prefix) || pathname.includes(prefix));
}

export function useLogout() {
  const router = useRouter();
  return async function logout() {
    const token = getToken();
    if (token) {
      await fetch(apiUrl("/api/auth/logout"), {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
    }
    clearSession();
    router.replace("/login");
  };
}

export function RoleShell({
  role,
  title,
  children,
}: {
  role: string;
  title: string;
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const [ready, setReady] = useState(false);
  const [openTickets, setOpenTickets] = useState(0);
  const [unread, setUnread] = useState(0);
  const [companyName, setCompanyName] = useState("");
  const [avatarUrl, setAvatarUrl] = useState<string | null>(null);
  const items = navigation[role] ?? [];
  const notifications = bellHref[role] ?? "/login";
  const bellActive = pathname === notifications;

  useEffect(() => {
    const token = getToken();
    if (!token || getRole() !== role) {
      router.replace("/login");
      return;
    }
    setReady(true);
  }, [role, router]);

  useEffect(() => {
    if (!ready) return;
    apiFetch("/api/notifications", { headers: authHeaders() })
      .then(async (response) => (response.ok ? response.json() : []))
      .then((rows: { is_read: boolean }[]) => setUnread(rows.filter((row) => !row.is_read).length))
      .catch(() => setUnread(0));
  }, [ready, pathname]);

  useEffect(() => {
    if (!ready || role !== "platform_admin") return;
    apiFetch("/api/admin/complaints", { headers: authHeaders() })
      .then(async (response) => (response.ok ? response.json() : []))
      .then((rows: { reply_message: string | null }[]) => setOpenTickets(rows.filter((row) => !row.reply_message).length))
      .catch(() => setOpenTickets(0));
  }, [ready, role, pathname]);

  useEffect(() => {
    if (!ready) return;
    apiFetch("/api/auth/me", { headers: authHeaders() })
      .then(async (response) => (response.ok ? response.json() : null))
      .then((body: { avatar_url?: string | null } | null) => setAvatarUrl(body?.avatar_url ?? null))
      .catch(() => setAvatarUrl(null));
  }, [ready, pathname]);

  useEffect(() => {
    function onProfile(event: Event) {
      const detail = (event as CustomEvent<{ avatar_url?: string | null }>).detail;
      if (detail && "avatar_url" in detail) setAvatarUrl(detail.avatar_url ?? null);
    }
    window.addEventListener("eshtrakei-profile", onProfile);
    return () => window.removeEventListener("eshtrakei-profile", onProfile);
  }, []);

  useEffect(() => {
    if (!ready || role !== "company_manager") return;
    apiFetch("/api/company/me", { headers: authHeaders() })
      .then(async (response) => (response.ok ? response.json() : null))
      .then((body: { name?: string } | null) => setCompanyName(body?.name ?? ""))
      .catch(() => setCompanyName(""));
  }, [ready, role, pathname]);

  if (!ready) return null;

  const links = items.map((item) => {
    const active = isActive(pathname, item);
    return { item, active };
  });
  const badge = role === "company_manager" && companyName ? `${companyName} - ${ar.managerAccount}` : headerBadge[role];

  return (
    <div className="min-h-full bg-surface text-on-surface">
      <header className="fixed inset-x-0 top-0 z-50 bg-surface/85 backdrop-blur-xl lg:ps-72">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 lg:h-20 lg:px-8">
          <div className="flex min-w-0 items-center gap-3">
            <span className="flex h-8 w-8 shrink-0 items-center justify-center overflow-hidden rounded-full bg-primary text-white">
              {avatarUrl ? <img src={apiUrl(avatarUrl)} alt="" className="h-full w-full object-cover" /> : <Icon name="person" className="text-[18px]" />}
            </span>
            <div className="min-w-0">
              <h1 className="truncate text-lg font-extrabold leading-tight">{title}</h1>
              {badge ? (
                <span className={`mt-0.5 inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-[11px] font-bold ${role === "company_manager" ? "bg-surface-container text-secondary" : "bg-secondary-fixed text-on-secondary-fixed"}`}>
                  <span className="h-1.5 w-1.5 rounded-full bg-tertiary-container" />
                  {badge}
                </span>
              ) : null}
            </div>
          </div>
          <div className="flex items-center gap-1">
            <ThemeToggle compact />
            <Link
            href={notifications}
            aria-label={ar.notifications}
            aria-current={bellActive ? "page" : undefined}
            className="relative flex h-11 w-11 items-center justify-center rounded-full text-secondary transition hover:bg-surface-container"
          >
            <Icon name="notifications" className="text-[24px]" />
            {unread > 0 ? <span className="absolute top-1.5 left-1.5 flex h-4 min-w-4 items-center justify-center rounded-full bg-primary-container px-1 text-[10px] font-bold text-white">{unread}</span> : null}
          </Link>
          </div>
        </div>
      </header>

      <aside className="fixed inset-y-0 start-0 z-40 hidden w-72 flex-col bg-surface-lowest px-4 py-6 shadow-[0_10px_25px_-5px_rgba(30,58,95,0.08)] lg:flex">
        <Link href={items[0]?.href ?? "/"} className="mb-8 flex items-center gap-3 px-2">
          <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-primary-container text-white">
            <Icon name="wifi" className="text-[22px]" />
          </span>
          <span className="text-lg font-extrabold">{ar.appName}</span>
        </Link>
        <nav className="flex flex-1 flex-col gap-1.5">
          {links.map(({ item, active }) => (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 rounded-2xl px-3 py-3 text-sm font-bold transition ${
                active ? "bg-[#213145] text-[#eaf1ff] shadow-md dark:bg-[#2a4060]" : "text-secondary hover:bg-surface-low"
              }`}
            >
              <span className="relative">
                <Icon name={item.icon} className="text-[22px]" />
                {item.href === "/admin/complaints" && openTickets > 0 ? (
                  <span className="absolute -top-2 -start-2 flex h-[18px] min-w-[18px] items-center justify-center rounded-full bg-error px-1 text-[10px] text-white">{openTickets}</span>
                ) : null}
              </span>
              {item.label}
            </Link>
          ))}
        </nav>
      </aside>

      <div className="lg:ps-72">
        <main className="mx-auto flex w-full max-w-6xl flex-col gap-4 px-4 pb-28 pt-20 lg:px-8 lg:pb-10 lg:pt-24">{children}</main>
      </div>

      <nav className={`fixed inset-x-0 bottom-0 z-50 lg:hidden ${role === "company_manager" ? "pointer-events-none px-4 pb-3" : "rounded-t-3xl bg-surface-lowest/90 pb-[env(safe-area-inset-bottom)] shadow-[0_-8px_24px_rgba(30,58,95,0.08)] backdrop-blur-xl"}`}>
        <div className={`mx-auto flex items-center justify-around ${role === "company_manager" ? "pointer-events-auto h-auto max-w-md rounded-full bg-surface-lowest/90 p-1.5 shadow-[0_12px_32px_rgba(30,58,95,0.12)] backdrop-blur-xl" : "h-20 px-3"}`}>
          {links.map(({ item, active }) => (
            <Link
              key={item.href}
              href={item.href}
              className={`flex min-h-12 min-w-16 items-center justify-center font-bold transition ${
                role === "company_manager"
                  ? `flex-1 flex-row gap-2 rounded-full px-4 py-3 text-sm ${active ? "bg-secondary text-on-secondary shadow-md" : "text-secondary"}`
                  : role === "client"
                    ? `flex-col gap-1 rounded-full px-3 py-1.5 text-[11px] ${active ? "bg-inverse-surface text-inverse-on-surface" : "text-secondary"}`
                    : `flex-col gap-1 rounded-2xl px-3 py-2 text-[11px] ${active ? "bg-[#213145] text-[#eaf1ff] shadow-md dark:bg-[#2a4060]" : "text-secondary"}`
              }`}
            >
              <span className="relative">
                <Icon name={item.icon} className="text-[24px]" />
                {item.href === "/admin/complaints" && openTickets > 0 ? (
                  <span className="absolute -top-1.5 -start-2 flex h-[18px] min-w-[18px] items-center justify-center rounded-full bg-error px-1 text-[10px] text-white">{openTickets}</span>
                ) : null}
              </span>
              <span>{item.label}</span>
            </Link>
          ))}
        </div>
      </nav>
    </div>
  );
}
