export function QuotaRing({ totalGb, usedGb = 0 }: { totalGb: number; usedGb?: number }) {
  const safeTotal = totalGb > 0 ? totalGb : 0;
  const used = Math.min(Math.max(usedGb, 0), safeTotal || 0);
  const remaining = Math.max(safeTotal - used, 0);
  const ratio = safeTotal === 0 ? 0 : used / safeTotal;
  const ticks = 48;
  const active = Math.round(ratio * ticks);

  return (
    <div className="relative mx-auto flex h-56 w-56 items-center justify-center sm:h-64 sm:w-64">
      <svg className="h-full w-full -rotate-90" viewBox="0 0 200 200" aria-hidden="true">
        <circle cx="100" cy="100" r="82" fill="none" stroke="#E2E8F0" strokeWidth="12" strokeDasharray="2 10" strokeLinecap="round" />
        <circle
          cx="100"
          cy="100"
          r="82"
          fill="none"
          stroke="#1E3A5F"
          strokeWidth="12"
          strokeDasharray="2 10"
          strokeDashoffset={Math.max(0, (ticks - active) * 12)}
          strokeLinecap="round"
        />
        <circle cx="100" cy="100" r="92" fill="none" stroke="#F58220" strokeWidth="2" strokeDasharray="4 8" strokeOpacity="0.35" />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
        <span className="text-xs font-medium text-secondary">المتبقي</span>
        <div className="text-[28px] font-extrabold leading-9 text-on-surface" dir="ltr">
          GB {remaining}
        </div>
        <span className="mt-1 text-[11px] font-semibold text-primary-container">من إجمالي {safeTotal} GB</span>
      </div>
    </div>
  );
}
