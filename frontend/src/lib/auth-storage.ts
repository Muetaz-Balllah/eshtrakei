const TOKEN_KEY = "access_token";
const ROLE_KEY = "role";

export function saveSession(token: string, role: string) {
  sessionStorage.setItem(TOKEN_KEY, token);
  sessionStorage.setItem(ROLE_KEY, role);
}

export function clearSession() {
  sessionStorage.removeItem(TOKEN_KEY);
  sessionStorage.removeItem(ROLE_KEY);
}

export function getToken() {
  return sessionStorage.getItem(TOKEN_KEY);
}

export function getRole() {
  return sessionStorage.getItem(ROLE_KEY);
}
