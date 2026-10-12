"use client";

import { FormEvent, useEffect, useState } from "react";
import { fieldClass, Icon, Notice, primaryButton } from "@/components/ui/ui";
import { apiFetch, apiUrl, authHeaders } from "@/lib/api";
import { passwordIsStrong } from "@/lib/password";
import { ar } from "@/messages/ar";

type Me = { full_name: string; phone: string | null; avatar_url: string | null };

const rowClass = "flex w-full items-center justify-between gap-3 rounded-2xl p-3 text-start transition hover:bg-surface-low";

export function InlineAccount() {
  const [me, setMe] = useState<Me | null>(null);
  const [open, setOpen] = useState<"profile" | "password" | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [notice, setNotice] = useState("");

  useEffect(() => {
    apiFetch("/api/auth/me", { headers: authHeaders() }).then(async (response) => {
      if (response.ok) setMe(await response.json());
    });
  }, []);

  function toggle(next: "profile" | "password") {
    setOpen(open === next ? null : next);
    setNotice("");
  }

  async function saveProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const response = await apiFetch("/api/auth/profile", {
      method: "PUT",
      headers: { ...authHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({ full_name: data.get("full_name"), phone: data.get("phone") }),
    });
    const body = await response.json();
    if (!response.ok) {
      setNotice(body.message);
      return;
    }
    const file = data.get("image");
    let profile = body;
    if (file instanceof File && file.size > 0) {
      const upload = new FormData();
      upload.set("image", file);
      const photo = await fetch(apiUrl("/api/auth/avatar"), { method: "POST", headers: authHeaders(), body: upload });
      const saved = await photo.json();
      if (!photo.ok) {
        setNotice(saved.message);
        return;
      }
      profile = saved;
    }
    setMe(profile);
    window.dispatchEvent(new CustomEvent("eshtrakei-profile", { detail: profile }));
    setPreview(null);
    setNotice(ar.save);
    setOpen(null);
  }

  async function savePassword(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    if (String(data.get("new_password") ?? "") !== String(data.get("confirm_password") ?? "")) {
      setNotice(ar.passwordMismatch);
      return;
    }
    if (!passwordIsStrong(String(data.get("new_password") ?? ""))) {
      setNotice(ar.passwordHint);
      return;
    }
    const response = await apiFetch("/api/auth/password", {
      method: "POST",
      headers: { ...authHeaders(), "Content-Type": "application/json" },
      body: JSON.stringify({ current_password: data.get("current_password"), new_password: data.get("new_password") }),
    });
    const body = await response.json();
    setNotice(body.message ?? ar.loginFailed);
    if (response.ok) {
      form.reset();
      setOpen(null);
    }
  }

  const photo = preview || (me?.avatar_url ? apiUrl(me.avatar_url) : "");

  return (
    <div className="flex flex-col gap-1">
      <button type="button" className={rowClass} onClick={() => toggle("profile")}>
        <span className="flex items-center gap-3">
          <span className="flex h-11 w-11 items-center justify-center overflow-hidden rounded-2xl bg-surface-container text-secondary">
            {photo ? <img src={photo} alt="" className="h-full w-full object-cover" /> : <Icon name="manage_accounts" className="text-[22px]" />}
          </span>
          <span>
            <span className="block font-extrabold">{ar.personalInfo}</span>
            <span className="text-sm text-secondary">{me?.full_name}</span>
          </span>
        </span>
        <Icon name={open === "profile" ? "expand_less" : "chevron_left"} className="text-secondary" />
      </button>
      {open === "profile" ? (
        <form onSubmit={saveProfile} className="mx-3 mb-3 flex flex-col gap-2 rounded-2xl bg-surface-low p-3">
          <input name="full_name" required defaultValue={me?.full_name} placeholder={ar.fullName} className={fieldClass} />
          <input name="phone" required defaultValue={me?.phone ?? ""} placeholder={ar.phone} className={fieldClass} />
          <input name="image" type="file" accept="image/png,image/jpeg,image/webp" className={fieldClass} onChange={(event) => setPreview(event.target.files?.[0] ? URL.createObjectURL(event.target.files[0]) : null)} />
          {preview ? <img src={preview} alt="" className="h-16 w-16 rounded-full object-cover" /> : null}
          <button className={`${primaryButton} w-fit transition hover:opacity-90`} type="submit">{ar.save}</button>
        </form>
      ) : null}
      <button type="button" className={rowClass} onClick={() => toggle("password")}>
        <span className="flex items-center gap-3">
          <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-tertiary/15 text-tertiary"><Icon name="security" className="text-[22px]" /></span>
          <span>
            <span className="block font-extrabold">{ar.passwordSecurity}</span>
            <span className="text-sm text-secondary">{ar.changePassword}</span>
          </span>
        </span>
        <Icon name={open === "password" ? "expand_less" : "chevron_left"} className="text-secondary" />
      </button>
      {open === "password" ? (
        <form onSubmit={savePassword} className="mx-3 mb-3 flex flex-col gap-2 rounded-2xl bg-surface-low p-3">
          <input name="current_password" required type="password" placeholder={ar.currentPassword} className={fieldClass} />
          <input name="new_password" required minLength={8} type="password" placeholder={ar.newPassword} className={fieldClass} />
          <input name="confirm_password" required type="password" placeholder={ar.confirmPassword} className={fieldClass} />
          <p className="text-xs font-medium text-secondary">{ar.passwordHint}</p>
          <button className={`${primaryButton} w-fit transition hover:opacity-90`} type="submit">{ar.changePassword}</button>
        </form>
      ) : null}
      {notice ? <Notice>{notice}</Notice> : null}
    </div>
  );
}
