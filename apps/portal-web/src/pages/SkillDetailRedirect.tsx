import { Navigate, useParams } from "react-router-dom";

export default function SkillDetailRedirect() {
  /**
   * 交互约定：
   * - 门户详情的标准入口是 Marketplace 抽屉（query 参数驱动）。
   * - 此路由用于兼容历史深链，统一重定向到 `/categories?skill=<slug>&usage=agent`。
   */
  const { slug } = useParams();
  return <Navigate to={slug ? `/categories?skill=${slug}&usage=agent` : "/categories"} replace />;
}

