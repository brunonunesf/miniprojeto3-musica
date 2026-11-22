import { apiPost } from "@/lib/api";

const CHAVE_TOKEN = "token";

export async function entrar(username: string, password: string): Promise<void> {
  const { token } = await apiPost<{ token: string }>("/auth/login", { username, password });
  localStorage.setItem(CHAVE_TOKEN, token);
  window.dispatchEvent(new Event("auth"));
}

export function sair(): void {
  localStorage.removeItem(CHAVE_TOKEN);
  window.dispatchEvent(new Event("auth"));
}

export function temToken(): boolean {
  return localStorage.getItem(CHAVE_TOKEN) !== null;
}
