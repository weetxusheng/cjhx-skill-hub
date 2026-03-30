/**
 * 模块约定：
 * - 前台统一 HTTP 封装入口，负责 API 根路径、错误解包和 Bearer 令牌附加。
 * - portal 页面、抽屉和组件统一经由这里访问 JSON API，不直接散落 `fetch`。
 * - access 过期返回 401 时，若存在 refresh_token，则自动 `/auth/refresh` 换新并重试一次。
 */
import type { PortalUser } from "../store/auth";
import { usePortalAuthStore } from "../store/auth";
import { showSessionInvalidModal } from "./sessionInvalidModal";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api";
const ADMIN_WEB_URL = import.meta.env.VITE_ADMIN_WEB_URL ?? "http://127.0.0.1:5174";

type RequestOptions = RequestInit & {
  token?: string | null;
};

type RefreshPayload = {
  access_token: string;
  refresh_token: string;
  user: PortalUser;
};

let refreshPromise: Promise<string | undefined> | null = null;

async function postRefresh(refreshToken: string): Promise<RefreshPayload> {
  const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
  const payload = await response.json().catch(() => ({ message: "请求失败" }));
  if (!response.ok) {
    const detail = (payload as { detail?: unknown; message?: string }).detail;
    const msg =
      typeof detail === "string" ? detail : (payload as { message?: string }).message ?? "请求失败";
    throw new Error(msg);
  }
  return (payload as { data: RefreshPayload }).data;
}

async function refreshSessionAndGetAccessToken(): Promise<string | undefined> {
  if (refreshPromise) {
    return refreshPromise;
  }
  refreshPromise = (async () => {
    try {
      const { refreshToken, setSession } = usePortalAuthStore.getState();
      if (!refreshToken) {
        usePortalAuthStore.getState().clearSession();
        return undefined;
      }
      const data = await postRefresh(refreshToken);
      setSession({
        accessToken: data.access_token,
        refreshToken: data.refresh_token,
        user: data.user,
      });
      return data.access_token;
    } catch {
      usePortalAuthStore.getState().clearSession();
      return undefined;
    } finally {
      refreshPromise = null;
    }
  })();
  return refreshPromise;
}

function shouldTryRefresh(path: string): boolean {
  if (path === "/auth/refresh" || path.startsWith("/auth/login")) {
    return false;
  }
  return true;
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { token, headers, ...rest } = options;
  const isFormData = typeof FormData !== "undefined" && rest.body instanceof FormData;

  const doFetch = (bearer: string | null | undefined) =>
    fetch(`${API_BASE_URL}${path}`, {
      ...rest,
      headers: {
        ...(isFormData ? {} : { "Content-Type": "application/json" }),
        ...(bearer ? { Authorization: `Bearer ${bearer}` } : {}),
        ...headers,
      },
    });

  let response = await doFetch(token);

  if (response.status === 401 && token && shouldTryRefresh(path)) {
    const newAccess = await refreshSessionAndGetAccessToken();
    if (newAccess) {
      response = await doFetch(newAccess);
    }
  }

  if (response.status === 401 && token) {
    showSessionInvalidModal();
    usePortalAuthStore.getState().clearSession();
    throw new Error("登录已失效，请关闭页面后从 OA 首页重新进入技能广场。");
  }

  const payload = await response.json().catch(() => ({ message: "请求失败" }));
  if (!response.ok) {
    const detail = (payload as { detail?: unknown; message?: string }).detail;
    const msg =
      typeof detail === "string" ? detail : (payload as { message?: string }).message ?? "请求失败";
    throw new Error(msg);
  }
  return (payload as { data: T }).data as T;
}

export { ADMIN_WEB_URL, API_BASE_URL };
