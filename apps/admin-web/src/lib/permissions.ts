export type AdminUserIdentity = {
  roles: string[];
  permissions: string[];
};

export function hasPermission(user: AdminUserIdentity | null | undefined, permission: string) {
  return Boolean(user?.permissions?.includes(permission));
}
