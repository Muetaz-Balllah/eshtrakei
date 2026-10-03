"use client";

import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { CoverageMap, MapTower } from "@/components/map/coverage-map";
import { RoleShell } from "@/components/shell/role-shell";
import { apiFetch, apiUrl, authHeaders } from "@/lib/api";
import { readCompanyId, writeCompanyId } from "@/lib/selected-company";
import { ar } from "@/messages/ar";

type Company = { id: number; name: string };
type Tower = MapTower & { company_id: number };

export default function ClientCoveragePage() {
  const search = useSearchParams();
  const [companies, setCompanies] = useState<Company[]>([]);
  const [towers, setTowers] = useState<Tower[]>([]);
  const [selected, setSelected] = useState<number | null>(null);

  useEffect(() => {
    const headers = authHeaders();
    const queryCompany = Number(search.get("company"));
    fetch(apiUrl("/api/companies"), { headers }).then(async (response) => {
      const rows: Company[] = response.ok ? await response.json() : [];
      setCompanies(rows);
      const saved = readCompanyId();
      const initial = rows.find((row) => row.id === queryCompany)?.id ?? rows.find((row) => row.id === saved)?.id ?? rows[0]?.id ?? null;
      setSelected(initial);
    });
    apiFetch("/api/towers", { headers }).then(async (response) => {
      if (response.ok) setTowers(await response.json());
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function choose(id: number) {
    setSelected(id);
    writeCompanyId(id);
  }

  const visible = useMemo(() => towers.filter((tower) => tower.company_id === selected), [towers, selected]);
  const company = companies.find((row) => row.id === selected);

  return (
    <RoleShell role="client" title={ar.coverage}>
      <div className="flex gap-2 overflow-x-auto pb-1">
        {companies.map((row) => (
          <button key={row.id} type="button" onClick={() => choose(row.id)} className={`shrink-0 rounded-full px-3 py-1.5 text-sm font-bold ${row.id === selected ? "bg-inverse-surface text-inverse-on-surface" : "bg-surface-lowest text-secondary"}`}>
            {row.name}
          </button>
        ))}
      </div>
      <p className="text-sm font-bold text-secondary">{company?.name}</p>
      <CoverageMap towers={visible} />
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {visible.map((tower) => (
          <article key={tower.id} className="rounded-3xl bg-surface-lowest p-4 shadow-sm">
            <p className="text-sm font-bold text-secondary">{tower.company_name}</p>
            <h2 className="font-extrabold">{tower.name}</h2>
            <p className="text-sm" dir="ltr">{tower.radius_meters} m</p>
          </article>
        ))}
      </div>
    </RoleShell>
  );
}
