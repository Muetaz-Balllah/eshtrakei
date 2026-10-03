export const fieldClass =
  "min-h-12 w-full rounded-2xl border border-outline-variant bg-surface-lowest px-4 text-on-surface outline-none transition placeholder:text-secondary/70 focus:border-primary-container focus:ring-2 focus:ring-primary-container/30";

export const primaryButton =
  "inline-flex min-h-12 items-center justify-center gap-2 rounded-2xl bg-primary-container px-5 text-sm font-bold text-white shadow-[0_8px_20px_-6px_rgba(245,130,32,0.55)] transition active:scale-[0.98]";

export const navyButton =
  "inline-flex min-h-12 items-center justify-center gap-2 rounded-2xl bg-inverse-surface px-5 text-sm font-bold text-inverse-on-surface transition active:scale-[0.98]";

export const ghostButton =
  "inline-flex min-h-11 items-center justify-center gap-2 rounded-2xl bg-surface-low px-4 text-sm font-bold text-secondary transition hover:bg-surface-container";

export const dangerButton =
  "inline-flex min-h-11 items-center justify-center gap-2 rounded-2xl bg-error px-4 text-sm font-bold text-white transition active:scale-[0.98]";

export const cardClass =
  "rounded-3xl bg-surface-lowest p-5 shadow-[0_10px_25px_-5px_rgba(30,58,95,0.07),0_4px_6px_-2px_rgba(30,58,95,0.03)] dark:shadow-[0_16px_36px_-18px_rgba(0,0,0,0.7)]";

export function Icon({ name, className = "" }: { name: string; className?: string }) {
  return <span className={`material-symbols-outlined ${className}`}>{name}</span>;
}

export function Badge({
  children,
  tone = "neutral",
}: {
  children: React.ReactNode;
  tone?: "neutral" | "ok" | "warn" | "bad";
}) {
  const tones = {
    neutral: "bg-surface-container text-secondary",
    ok: "bg-tertiary/15 text-tertiary",
    warn: "bg-[#ffdcc6] text-[#5b2a00]",
    bad: "bg-error-container text-error",
  };
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-bold ${tones[tone]}`}>
      {children}
    </span>
  );
}

export function SectionTitle({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <h2 className={`px-1 text-lg font-extrabold text-on-surface ${className}`}>{children}</h2>;
}

export function EmptyState({ children }: { children: React.ReactNode }) {
  return (
    <p className="rounded-2xl bg-surface-low px-4 py-6 text-center text-sm font-medium text-secondary">{children}</p>
  );
}

export function Notice({ children }: { children: React.ReactNode }) {
  return (
    <p className="rounded-2xl bg-secondary-fixed px-4 py-3 text-sm font-semibold text-on-secondary-fixed">{children}</p>
  );
}
