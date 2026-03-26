import { create } from "zustand";

type UserInfo = {
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
  setSession: ({ accessToken, refreshToken, user }) => {
    const nextState = { accessToken, refreshToken, user };
    if (typeof window !== "undefined") {
      window.localStorage.setItem(STORAGE_KEY, JSON.stringify(nextState));
    }
    set(nextState);
  },
  clearSession: () => {
    if (typeof window !== "undefined") {
      window.localStorage.removeItem(STORAGE_KEY);
    }
    set({ accessToken: null, refreshToken: null, user: null });
  },
}));
