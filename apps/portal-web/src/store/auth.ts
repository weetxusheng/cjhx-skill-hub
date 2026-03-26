import { create } from "zustand";

type PortalUser = {
  id: string;
  username: string;
  display_name: string;
  email: string | null;
  status: "active" | "disabled";
  roles: string[];
  permissions: string[];
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
