"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { AuthFrame } from "@/components/shell/auth-frame";
import { fieldClass, Notice, primaryButton } from "@/components/ui/ui";
import { apiUrl } from "@/lib/api";
import { ar } from "@/messages/ar";

export default function JoinCompanyPage() {
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    const response = await fetch(apiUrl("/api/join-requests"), { method: "POST", body: new FormData(event.currentTarget) });
    const body = await response.json();
    if (!response.ok) {
      setError(body.message ?? ar.loginFailed);
      return;
    }
    setSent(true);
  }

  return (
    <AuthFrame title={ar.joinCompany}>
      {sent ? (
        <Notice>{ar.requestSent}</Notice>
      ) : (
        <form onSubmit={onSubmit} className="flex w-full flex-col gap-4">
          <label className="flex flex-col gap-2 text-sm font-bold text-secondary">
            {ar.companyName}
            <input name="name" required className={fieldClass} />
          </label>
          <label className="flex flex-col gap-2 text-sm font-bold text-secondary">
            {ar.description}
            <textarea name="description" className={fieldClass} rows={4} />
          </label>
          <label className="flex flex-col gap-2 text-sm font-bold text-secondary">
            {ar.phone}
            <input name="phone" required className={fieldClass} />
          </label>
          <label className="flex flex-col gap-2 text-sm font-bold text-secondary">
            {ar.logo}
            <input name="logo" type="file" accept="image/png,image/jpeg,image/webp" className={`${fieldClass} py-3`} />
          </label>
          {error ? <p className="rounded-2xl bg-error-container px-4 py-3 text-sm font-semibold text-error">{error}</p> : null}
          <button type="submit" className={primaryButton}>
            {ar.submitRequest}
          </button>
        </form>
      )}
      <Link href="/login" className="mt-4 inline-block text-sm font-bold text-secondary hover:text-primary">
        {ar.haveAccount}
      </Link>
    </AuthFrame>
  );
}
