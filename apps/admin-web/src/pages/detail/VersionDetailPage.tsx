import { useParams } from "react-router-dom";

import { AdminVersionDetailPanel } from "../../components/AdminVersionDetailPanel";

/**
 * 技能版本详情（独立路由页）
 *
 * 交互约定：
 * - 将路由参数 `versionId` 交给 `AdminVersionDetailPanel`，具体加载/空态/错误态/审核操作在面板内实现。
 * - `versionId` 缺失时传入 `null`，由面板决定如何提示。
 * - 独立页加载成功后顶部提供「返回技能详情」链至 `/skills/:skillId`。
 */
export function VersionDetailPage() {
  const { versionId } = useParams();
  return <AdminVersionDetailPanel versionId={versionId ?? null} variant="page" />;
}
