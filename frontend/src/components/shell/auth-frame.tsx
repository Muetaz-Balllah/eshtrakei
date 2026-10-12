import { ThemeToggle } from "@/components/shell/theme-toggle";
import { cardClass, Icon } from "@/components/ui/ui";
import { ar } from "@/messages/ar";

export function AuthFrame({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="min-h-dvh bg-surface lg:grid lg:grid-cols-[minmax(0,1.05fr)_minmax(0,0.95fr)] lg:grid-rows-[minmax(100dvh,auto)]">
      <section className="relative hidden overflow-hidden bg-inverse-surface text-inverse-on-surface lg:flex lg:h-full lg:flex-col lg:justify-between lg:self-stretch lg:p-12">
        <div className="pointer-events-none absolute -start-16 -top-16 h-64 w-64 rounded-full bg-primary-container/30 blur-3xl" />
        <div className="pointer-events-none absolute bottom-0 end-0 h-48 w-48 rounded-full bg-secondary/40 blur-3xl" />
        <div className="relative">
          <span className="mb-8 flex h-14 w-14 items-center justify-center rounded-2xl bg-primary-container text-white shadow-lg">
            <Icon name="wifi" className="text-[30px]" />
          </span>
          <h1 className="text-4xl font-extrabold leading-tight">{ar.appName}</h1>
          <p className="mt-4 max-w-sm text-lg font-medium text-secondary-fixed">منصة إدارة اشتراكات الإنترنت</p>
        </div>
        <p className="relative text-sm text-secondary-fixed/80">حسابات الزبائن، مديري الشركات، ومدير المنصة</p>
      </section>
      <div className="flex min-h-dvh flex-col px-4 py-6 sm:px-8 lg:h-full lg:min-h-full">
        <div className="mb-6 flex items-center justify-between lg:justify-end">
          <div className="flex items-center gap-2 lg:hidden">
            <span className="flex h-10 w-10 items-center justify-center rounded-2xl bg-primary-container text-white">
              <Icon name="wifi" className="text-[22px]" />
            </span>
            <span className="text-xl font-extrabold">{ar.appName}</span>
          </div>
          <ThemeToggle />
        </div>
        <div className="mx-auto flex w-full max-w-md flex-1 flex-col justify-center pb-8">
          <section className={cardClass}>
            <h2 className="mb-6 text-2xl font-extrabold">{title}</h2>
            {children}
          </section>
        </div>
      </div>
    </div>
  );
}
