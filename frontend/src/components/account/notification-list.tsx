"use client";

import { useEffect, useState } from "react";
import { RoleShell } from "@/components/shell/role-shell";
import { cardClass, EmptyState, Icon } from "@/components/ui/ui";
import { apiFetch, authHeaders } from "@/lib/api";
import { ar } from "@/messages/ar";

type Note = { id: number; message: string; created_at: string; is_read: boolean };

export function NotificationList({ role }: { role: "client" | "platform_admin" | "company_manager" }) {
  const [rows, setRows] = useState<Note[]>([]);

  useEffect(() => {
    const headers = authHeaders();
    apiFetch("/api/notifications", { headers })
      .then((response) => (response.ok ? response.json() : []))
      .then(async (items: Note[]) => {
        setRows(items);
        if (items.some((row) => !row.is_read)) {
          await apiFetch("/api/notifications/read", { method: "POST", headers });
        }
      });
  }, []);

  return (
    <RoleShell role={role} title={ar.notifications}>
      {rows.length === 0 ? <EmptyState>{ar.noNotifications}</EmptyState> : null}
      <div className="grid gap-3 lg:grid-cols-2">
        {rows.map((row) => (
          <article key={row.id} className={`${cardClass} flex items-start gap-3`}>
            <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-secondary-fixed text-secondary">
              <Icon name="notifications" className="text-[22px]" />
            </span>
            <div>
              <p className="font-semibold">{row.message}</p>
              <p className="mt-1 text-xs text-secondary">{new Date(row.created_at).toLocaleString("ar")}</p>
            </div>
          </article>
        ))}
      </div>
    </RoleShell>
  );
}
