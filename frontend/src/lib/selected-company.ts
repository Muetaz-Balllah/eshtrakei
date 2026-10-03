const key = "client_company_id";

export function readCompanyId() {
  if (typeof window === "undefined") return null;
  const value = sessionStorage.getItem(key);
  const id = value ? Number(value) : NaN;
  return Number.isFinite(id) ? id : null;
}

export function writeCompanyId(id: number) {
  sessionStorage.setItem(key, String(id));
}
