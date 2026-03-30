/**
 * 模块约定：
 * - 管理后台统一 HTTP 封装与响应解包入口，页面和组件不得绕开它直接 `fetch` JSON API。
 * - 成功响应约定为 `{ data: T }`；失败统一抛 `Error`，由页面或 mutation 负责展示。
 *
 * - `VITE_API_BASE_URL` 为同源 API 根路径（默认本地 `.../api`），与 Vite 代理一致。
 * - 成功响应约定为 `{ data: T }`；失败时读取 `detail` 或 `message` 抛出 `Error`，由页面/mutation 展示。
 * - `body` 为 `FormData` 时不设置 `Content-Type`，以便浏览器带 multipart boundary；否则默认 `application/json`。
 * - 传入 `token` 时附加 `Authorization: Bearer`，无 token 的请求用于登录等匿名接口。
 * - access 过期返回 401 时，若存在 refresh_token，则自动调用 `/auth/refresh` 换新并重试一次（并发请求共用一个刷新 Promise）。
 */
import type { UserInfo } from "../store/auth";
import { useAuthStore } from "../store/auth";
import { showSessionInvalidModal } from "./sessionInvalidModal";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api";

type RequestOptions = RequestInit & {
  /** 传入时设置 Bearer；匿名接口传 `null`/`undefined`。 */
  token?: string | null;
};

type RefreshPayload = {
  access_token: string;
  refresh_token: string;
  user: UserInfo;
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
      const { refreshToken, setSession } = useAuthStore.getState();
      if (!refreshToken) {
        useAuthStore.getState().clearSession();
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
      useAuthStore.getState().clearSession();
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

/**
 * 请求 JSON API：`path` 为相对 `API_BASE_URL` 的路径（如 `/auth/me`）。
 *
 * - `options` 透传 `fetch`（除会合并 `headers`）；`method` 默认 GET。
 * - 成功时返回 `data` 字段；非 2xx 或解析失败时抛出带服务端文案的 `Error`。
 */
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
    useAuthStore.getState().clearSession();
    throw new Error("登录已失效，请关闭页签后重新进入或重新登录。");
  }

  const payload = await response.json().catch(() => ({ message: "请求失败" }));
  if (!response.ok) {
    throw new Error(
      typeof (payload as { detail?: unknown }).detail === "string"
        ? ((payload as { detail: string }).detail)
        : (payload as { message?: string }).message ?? "请求失败",
    );
  }

  return (payload as { data: T }).data as T;
}

/**
 * 下载二进制响应（如版本 ZIP）：带 Bearer，从 `Content-Disposition` 解析文件名并触发浏览器下载。
 */
export async function downloadBinary(path: string, token: string): Promise<void> {
  const doFetch = (bearer: string) =>
    fetch(`${API_BASE_URL}${path}`, {
      headers: { Authorization: `Bearer ${bearer}` },
    });

  let response = await doFetch(token);

  if (response.status === 401 && shouldTryRefresh(path)) {
    const newAccess = await refreshSessionAndGetAccessToken();
    if (newAccess) {
      response = await doFetch(newAccess);
    }
  }

  if (response.status === 401) {
    showSessionInvalidModal();
    useAuthStore.getState().clearSession();
    throw new Error("登录已失效，请关闭页签后重新进入或重新登录。");
  }

  if (!response.ok) {
    const payload = await response.json().catch(() => ({ message: "下载失败" }));
    const detail = (payload as { detail?: unknown; message?: string }).detail;
    const msg =
      typeof detail === "string"
        ? detail
        : (payload as { message?: string }).message ?? "下载失败";
    throw new Error(msg);
  }
  const cd = response.headers.get("Content-Disposition");
  let filename = "skill-package.zip";
  if (cd) {
    const star = /filename\*=UTF-8''([^;]+)/i.exec(cd);
    const quoted = /filename="([^"]+)"/i.exec(cd);
    if (star) {
      filename = decodeURIComponent(star[1].trim());
    } else if (quoted) {
      filename = quoted[1];
    }
  }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}

export { API_BASE_URL };
