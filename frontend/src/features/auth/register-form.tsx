"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { fieldClass, primaryButton } from "@/components/ui/ui";
import { apiUrl } from "@/lib/api";
import { saveSession } from "@/lib/auth-storage";
import { ar } from "@/messages/ar";

export function RegisterForm() {
  const router = useRouter();
  const [error, setError] = useState("");
  const [form, setForm] = useState({ full_name: "", city: "", phone: "", email: "", password: "" });

  function set(key: string, value: string) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    const response = await fetch(apiUrl("/api/auth/register"), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form),
    });
    const body = await response.json();
    if (!response.ok) {
      setError(body.message ?? ar.loginFailed);
      return;
    }
    saveSession(body.access_token, body.role);
    router.push("/client/companies");
  }

  return (
    <form onSubmit={onSubmit} className="flex w-full flex-col gap-4">
      <label className="flex flex-col gap-2 text-sm font-bold text-secondary">
        {ar.fullName}
        <input required className={fieldClass} value={form.full_name} onChange={(e) => set("full_name", e.target.value)} />
      </label>
      <div className="grid gap-4 sm:grid-cols-2">
        <label className="flex flex-col gap-2 text-sm font-bold text-secondary">
          {ar.city}
          <input required className={fieldClass} value={form.city} onChange={(e) => set("city", e.target.value)} />
        </label>
        <label className="flex flex-col gap-2 text-sm font-bold text-secondary">
          {ar.phone}
          <input required className={fieldClass} value={form.phone} onChange={(e) => set("phone", e.target.value)} />
        </label>
      </div>
      <label className="flex flex-col gap-2 text-sm font-bold text-secondary">
        {ar.email}
        <input required type="email" className={fieldClass} value={form.email} onChange={(e) => set("email", e.target.value)} />
      </label>
      <label className="flex flex-col gap-2 text-sm font-bold text-secondary">
        {ar.password}
        <input required type="password" minLength={8} className={fieldClass} value={form.password} onChange={(e) => set("password", e.target.value)} />
        <span className="text-xs font-medium text-secondary">{ar.passwordHint}</span>
      </label>
      {error ? <p className="rounded-2xl bg-error-container px-4 py-3 text-sm font-semibold text-error">{error}</p> : null}
      <button type="submit" className={primaryButton}>
        {ar.register}
      </button>
      <Link href="/login" className="text-center text-sm font-bold text-secondary hover:text-primary">
        {ar.haveAccount}
      </Link>
    </form>
  );
}
