"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { fieldClass, primaryButton } from "@/components/ui/ui";
import { apiFetch } from "@/lib/api";
import { saveSession } from "@/lib/auth-storage";
import { ar } from "@/messages/ar";

const homes: Record<string, string> = {
  platform_admin: "/admin/companies",
  company_manager: "/company",
  client: "/client/companies",
};

export function LoginForm() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError("");
    let response: Response;
    try {
      response = await apiFetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
    } catch {
      setError(ar.serverUnreachable);
      return;
    }
    if (!response.ok) {
      setError(ar.loginFailed);
      return;
    }
    const body = await response.json();
    saveSession(body.access_token, body.role);
    router.push(homes[body.role] ?? "/login");
  }

  return (
    <form onSubmit={onSubmit} className="flex w-full flex-col gap-4">
      <label className="flex flex-col gap-2 text-sm font-bold text-secondary">
        {ar.email}
        <input
          type="email"
          required
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          className={fieldClass}
        />
      </label>
      <label className="flex flex-col gap-2 text-sm font-bold text-secondary">
        {ar.password}
        <input
          type="password"
          required
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          className={fieldClass}
        />
      </label>
      {error ? <p className="rounded-2xl bg-error-container px-4 py-3 text-sm font-semibold text-error">{error}</p> : null}
      <button type="submit" className={primaryButton}>
        {ar.login}
      </button>
      <Link href="/register" className="text-center text-sm font-bold text-secondary hover:text-primary">
        {ar.noAccount}
      </Link>
      <Link href="/join-company" className="text-center text-sm font-bold text-primary">
        {ar.joinCompany}
      </Link>
    </form>
  );
}
