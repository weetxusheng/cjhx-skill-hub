/**
 * 状态约定：
 * - 管理后台认证会话（Zustand + localStorage）的唯一持久化入口。
 * - 只保存 token 与用户摘要；权限真值以 `/auth/me` 校验结果为准。
 *
 * - 持久化键：`skill-hub-admin-auth`；存 `accessToken`、`refreshToken`、登录后缓存的 `user` 摘要。
 * - 刷新页后由 `readInitialState` 恢复；`clearSession` 同时清 localStorage 与内存，用于登出或 `/auth/me` 失败。
 * - 权威用户信息以 `App` 内 `useQuery(["me", accessToken])` 为准，必要时与此处缓存对齐。
 */
import { create } from "zustand";

export type UserInfo = {
  id: string;
  username: string;
  display_name: string;
  email: string | null;
  status: "active" | "disabled";
  roles: string[];
  permissions: string[];
  last_login_at: string | null;
};

type AuthState = {
  accessToken: string | null;
  refreshToken: string | null;
  user: UserInfo | null;
  setSession: (payload: { accessToken: string; refreshToken: string; user: UserInfo }) => void;
  clearSession: () => void;
};

const STORAGE_KEY = "skill-hub-admin-auth";

/** 从 localStorage 恢复会话；损坏或缺失时返回全 `null`（SSR 下同样安全）。 */
function readInitialState(): Pick<AuthState, "accessToken" | "refreshToken" | "user"> {
  if (typeof window === "undefined") {
    return { accessToken: null, refreshToken: null, user: null };
  }

  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return { accessToken: null, refreshToken: null, user: null };
    }
    return JSON.parse(raw) as Pick<AuthState, "accessToken" | "refreshToken" | "user">;
  } catch {
    return { accessToken: null, refreshToken: null, user: null };
  }
}

export const useAuthStore = create<AuthState>((set) => ({
  ...readInitialState(),

  /** 写入双令牌与用户摘要，并同步持久化到 `STORAGE_KEY`。 */
  setSession: ({ accessToken, refreshToken, user }) => {
    const nextState = { accessToken, refreshToken, user };
    if (typeof window !== "undefined") {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(nextState));
    }
    set(nextState);
  },

  /** 清除内存与 localStorage 中的会话；不单独请求后端登出（由调用方决定）。 */
  clearSession: () => {
    if (typeof window !== "undefined") {
      window.localStorage.removeItem(STORAGE_KEY);
    }
    set({ accessToken: null, refreshToken: null, user: null });
  },
}));
