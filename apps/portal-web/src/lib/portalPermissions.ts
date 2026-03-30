/**
 * 模块约定：
 * - 汇总前台 capability 判断，只看 `/auth/me` 下发的全局 permission。
 * - portal 不在这里推断后台工作台权限或 skill 级授权。
 */
import type { PortalUser } from "./portalTypes";

export function hasPermission(user: PortalUser | null, permission: string) {
  return Boolean(user?.permissions?.includes(permission));
}
