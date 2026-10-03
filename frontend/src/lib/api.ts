const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "";

export function apiUrl(path: string) {
  if (typeof window !== "undefined") {
    return `${window.location.origin}${path}`;
  }
  return `${API_URL || "http://127.0.0.1:8000"}${path}`;
}

export async function apiFetch(path: string, init?: RequestInit) {
  try {
    return await fetch(apiUrl(path), init);
  } catch {
    throw new Error("network");
  }
}

export function authHeaders(): HeadersInit {
  const token = sessionStorage.getItem("access_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}
