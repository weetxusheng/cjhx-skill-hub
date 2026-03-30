/**
 * 状态约定：
 * - 前台认证会话的唯一 Zustand 持久化入口，负责 access token、refresh token 和用户摘要恢复。
 * - 点赞、收藏、投稿等登录态判断均以这里的会话为入口，再由 `/auth/me` 校验补强。
 */
import { create } from "zustand";

export type PortalUser = {
  id: string;
  username: string;
  display_name: string;
  email: string | null;
  status: "active" | "disabled";
  roles: string[];
  permissions: string[];
  /** 与后端 `UserSummary` 对齐；前台可不展示 */
  last_login_at?: string | null;
};

type PortalAuthState = {
  accessToken: string | null;
  refreshToken: string | null;
  user: PortalUser | null;
  setSession: (payload: { accessToken: string; refreshToken: string; user: PortalUser }) => void;
  clearSession: () => void;
};

const STORAGE_KEY = "skill-hub-portal-auth";

function readInitialState(): Pick<PortalAuthState, "accessToken" | "refreshToken" | "user"> {
  if (typeof window === "undefined") {
    return { accessToken: null, refreshToken: null, user: null };
  }
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : { accessToken: null, refreshToken: null, user: null };
  } catch {
    return { accessToken: null, refreshToken: null, user: null };
  }
}

export const usePortalAuthStore = create<PortalAuthState>((set) => ({
  ...readInitialState(),
  setSession: ({ accessToken, refreshToken, user }) => {
    const nextState = { accessToken, refreshToken, user };
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(nextState));
    set(nextState);
  },
  clearSession: () => {
    window.localStorage.removeItem(STORAGE_KEY);
    set({ accessToken: null, refreshToken: null, user: null });
  },
}));
