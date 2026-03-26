const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api";
const ADMIN_WEB_URL = import.meta.env.VITE_ADMIN_WEB_URL ?? "http://127.0.0.1:5174";

type RequestOptions = RequestInit & {
  token?: string | null;
};

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { token, headers, ...rest } = options;
  const isFormData = typeof FormData !== "undefined" && rest.body instanceof FormData;
  const actualResponse = await fetch(`${API_BASE_URL}${path}`, {
    ...rest,
    headers: {
      ...(isFormData ? {} : { "Content-Type": "application/json" }),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
  });
  const payload = await actualResponse.json().catch(() => ({ message: "请求失败" }));
  if (!actualResponse.ok) {
    throw new Error(payload.detail ?? payload.message ?? "请求失败");
  }
  return payload.data as T;
}

export { ADMIN_WEB_URL, API_BASE_URL };
