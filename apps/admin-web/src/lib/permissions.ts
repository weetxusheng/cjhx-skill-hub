/**
 * 模块约定：
 * - 汇总后台前端使用的最小权限判断契约，不推断 skill 级授权，只看全局 capability。
 * - 页面、菜单、按钮显隐统一走这里，避免散落字符串判断。
 */
/** 后台鉴权所需的最小用户切片（与 `/auth/me` 返回对齐）。 */
export type AdminUserIdentity = {
  roles: string[];
  permissions: string[];
};

/**
 * 判断当前用户是否拥有指定全局权限码。
 *
 * - `user` 为空视为无权限；仅检查 `permissions` 数组，不含 skill 级 scope。
 */
export function hasPermission(user: AdminUserIdentity | null | undefined, permission: string) {
  return Boolean(user?.permissions?.includes(permission));
}
