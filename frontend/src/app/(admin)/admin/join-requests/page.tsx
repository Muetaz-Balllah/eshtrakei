"use client";

import Link from "next/link";
import { RoleShell } from "@/components/shell/role-shell";
import { cardClass, ghostButton } from "@/components/ui/ui";
import { ar } from "@/messages/ar";

export default function JoinRequestsPage() {
  return (
    <RoleShell role="platform_admin" title={ar.joinRequests}>
      <section className={`${cardClass} flex flex-col items-start gap-4`}>
        <p className="text-secondary">{ar.pending}</p>
        <Link href="/admin/companies" className={ghostButton}>{ar.adminHome}</Link>
      </section>
    </RoleShell>
  );
}
