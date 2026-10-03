"use client";

import { FormEvent, useEffect, useState } from "react";
import { cardClass, fieldClass, Notice, primaryButton } from "@/components/ui/ui";
import { apiFetch, authHeaders } from "@/lib/api";
import { ar } from "@/messages/ar";

type Me = { full_name: string; city: string | null; phone: string | null; email: string };

export function AccountForms() {
  const [me, setMe] = useState<Me | null>(null);
  const [notice, setNotice] = useState("");

  useEffect(() => {
    apiFetch("/api/auth/me", { headers: authHeaders() }).then(async (response) => {
      if (response.ok) setMe(await response.json());
    });
  }, []);

  async function saveProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const response = await apiFetch("/api/auth/profile", {
      method: "PUT",
      headers: { ...authHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({ full_name: form.get("full_name"), city: form.get("city"), phone: form.get("phone") }),
    });
    const body = await response.json();
    if (response.ok) setMe(body);
    setNotice(response.ok ? ar.save : body.message);
  }

  async function savePassword(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    const response = await apiFetch("/api/auth/password", {
      method: "POST",
      headers: { ...authHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({ current_password: form.get("current_password"), new_password: form.get("new_password") }),
    });
    const body = await response.json();
    setNotice(body.message ?? ar.loginFailed);
    if (response.ok) formElement.reset();
  }

  if (!me) return null;

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <form onSubmit={saveProfile} className={`${cardClass} flex flex-col gap-3`}>
        <h2 className="font-extrabold">{ar.fullName}</h2>
        <input name="full_name" required defaultValue={me.full_name} className={fieldClass} />
        <input name="city" required defaultValue={me.city ?? ""} placeholder={ar.city} className={fieldClass} />
        <input name="phone" required defaultValue={me.phone ?? ""} placeholder={ar.phone} className={fieldClass} />
        <p className="text-sm text-secondary" dir="ltr">{me.email}</p>
        <button className={`${primaryButton} w-fit`} type="submit">{ar.save}</button>
      </form>
      <form onSubmit={savePassword} className={`${cardClass} flex flex-col gap-3`}>
        <h2 className="font-extrabold">{ar.changePassword}</h2>
        <input name="current_password" required type="password" placeholder={ar.currentPassword} className={fieldClass} />
        <input name="new_password" required minLength={8} type="password" placeholder={ar.newPassword} className={fieldClass} />
        <button className={`${primaryButton} w-fit`} type="submit">{ar.changePassword}</button>
      </form>
      {notice ? <Notice>{notice}</Notice> : null}
    </div>
  );
}
