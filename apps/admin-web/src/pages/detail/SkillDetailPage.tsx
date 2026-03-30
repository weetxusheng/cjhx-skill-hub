import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Alert, Card, Col, Row, Skeleton, message } from "antd";
import { useParams } from "react-router-dom";

import { SkillUploadModal } from "../../components/SkillUploadModal";
import { apiRequest } from "../../lib/api";
import { useAuthStore } from "../../store/auth";
import { SkillEngagementRecordsSection } from "./_components/SkillEngagementRecordsSection";
import { SkillGrantsCard } from "./_components/SkillGrantsCard";
import { SkillOverviewSection } from "./_components/SkillOverviewSection";
import { SkillStatsCard } from "./_components/SkillStatsCard";
import { SkillTimelineSection } from "./_components/SkillTimelineSection";
import type {
  CategoryItem,
  RoleItem,
  SkillDetailResponse,
  SkillDownloadRecord,
  SkillFavoriteRecord,
  SkillGrantItem,
  SkillStatsOverview,
  SkillUpdateInput,
  UserItem,
} from "./skillDetailTypes";

/**
 * 工作台 - 技能主档详情（聚合页）
 *
 * 交互约定：
 * - 加载态：`detailQuery` 未就绪时用 Skeleton 占位；子区块在各自 props 就绪后渲染。
 * - 空态/错误态：`skillId` 缺失或详情失败时用 Alert；成功但子列表为空由各子组件 Empty/文案处理。
 * - 权限不足态：依赖接口返回的 `capabilities`（如 `manage_grants`、`manage_skill`）；无权限时子组件显示只读或禁用操作。
 *
 * 数据流：
 * - 主档 PATCH、上传新版本、授权增删等 mutation 成功后 `invalidateQueries` 刷新详情与关联列表。
 * - 统计窗口 `statsWindow` 仅影响运营数据请求参数；授权区与角色/用户选项独立 query。
 */
export function SkillDetailPage() {
  const { skillId } = useParams();
  const accessToken = useAuthStore((state) => state.accessToken);
  const queryClient = useQueryClient();
  const [uploadOpen, setUploadOpen] = useState(false);
  const [roleScope, setRoleScope] = useState<string>("reviewer");
  const [selectedRoleIds, setSelectedRoleIds] = useState<string[]>([]);
  const [userScope, setUserScope] = useState<string>("maintainer");
  const [selectedUserIds, setSelectedUserIds] = useState<string[]>([]);
  const [statsWindow, setStatsWindow] = useState<"7" | "30">("7");

  const detailQuery = useQuery({
    queryKey: ["admin-skill-detail", accessToken, skillId],
    enabled: Boolean(skillId && accessToken),
    queryFn: () => apiRequest<SkillDetailResponse>(`/admin/skills/${skillId}`, { token: accessToken }),
  });

  const categoriesQuery = useQuery({
    queryKey: ["admin-skill-detail-categories", accessToken],
    queryFn: () => apiRequest<CategoryItem[]>("/admin/categories/options", { token: accessToken }),
  });

  const rolesQuery = useQuery({
    queryKey: ["admin-skill-role-options", accessToken],
    enabled: Boolean(accessToken && detailQuery.data?.capabilities.manage_grants),
    queryFn: () => apiRequest<RoleItem[]>("/admin/roles/options", { token: accessToken }),
  });

  const usersQuery = useQuery({
    queryKey: ["admin-skill-user-options", accessToken],
    enabled: Boolean(accessToken && detailQuery.data?.capabilities.manage_grants),
    queryFn: () => apiRequest<UserItem[]>("/admin/users/options?status=active", { token: accessToken }),
  });

  const grantsQuery = useQuery({
    queryKey: ["admin-skill-grants", accessToken, skillId],
    enabled: Boolean(skillId && accessToken),
    queryFn: () => apiRequest<SkillGrantItem[]>(`/admin/skills/${skillId}/permissions`, { token: accessToken }),
  });

  const statsQuery = useQuery({
    queryKey: ["admin-skill-stats", accessToken, skillId],
    enabled: Boolean(skillId && accessToken),
    queryFn: () => apiRequest<SkillStatsOverview>(`/admin/skills/${skillId}/stats`, { token: accessToken }),
  });

  const favoritesQuery = useQuery({
    queryKey: ["admin-skill-favorites", accessToken, skillId],
    enabled: Boolean(skillId && accessToken && detailQuery.data?.capabilities.view_favorite_details),
    queryFn: () => apiRequest<SkillFavoriteRecord[]>(`/admin/skills/${skillId}/favorites`, { token: accessToken }),
  });

  const downloadsQuery = useQuery({
    queryKey: ["admin-skill-downloads", accessToken, skillId],
    enabled: Boolean(skillId && accessToken && detailQuery.data?.capabilities.view_download_details),
    queryFn: () => apiRequest<SkillDownloadRecord[]>(`/admin/skills/${skillId}/downloads`, { token: accessToken }),
  });

  const updateMutation = useMutation({
    mutationFn: (values: SkillUpdateInput) =>
      apiRequest(`/admin/skills/${skillId}`, {
        method: "PATCH",
        token: accessToken,
        body: JSON.stringify(values),
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["admin-skill-detail", accessToken, skillId] });
      await queryClient.invalidateQueries({ queryKey: ["admin-skill-list"] });
      message.success("技能主档已保存。");
    },
    onError: (error: Error) => {
      message.error(error.message);
    },
  });

  const roleGrantMutation = useMutation({
    mutationFn: () =>
      apiRequest<SkillGrantItem[]>(`/admin/skills/${skillId}/role-grants`, {
        method: "POST",
        token: accessToken,
        body: JSON.stringify({ target_ids: selectedRoleIds, permission_scope: roleScope }),
      }),
    onSuccess: async () => {
      setSelectedRoleIds([]);
      await queryClient.invalidateQueries({ queryKey: ["admin-skill-grants", accessToken, skillId] });
      message.success("角色授权已更新。");
    },
    onError: (error: Error) => {
      message.error(error.message);
    },
  });

  const userGrantMutation = useMutation({
    mutationFn: () =>
      apiRequest<SkillGrantItem[]>(`/admin/skills/${skillId}/user-grants`, {
        method: "POST",
        token: accessToken,
        body: JSON.stringify({ target_ids: selectedUserIds, permission_scope: userScope }),
      }),
    onSuccess: async () => {
      setSelectedUserIds([]);
      await queryClient.invalidateQueries({ queryKey: ["admin-skill-grants", accessToken, skillId] });
      message.success("指定用户授权已更新。");
    },
    onError: (error: Error) => {
      message.error(error.message);
    },
  });

  const deleteGrantMutation = useMutation({
    mutationFn: ({ grantId, targetType }: { grantId: string; targetType: "role" | "user" }) =>
      apiRequest(`/admin/skills/${skillId}/${targetType}-grants/${grantId}`, {
        method: "DELETE",
        token: accessToken,
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["admin-skill-grants", accessToken, skillId] });
      message.success("授权已移除。");
    },
    onError: (error: Error) => {
      message.error(error.message);
    },
  });

  const detail = detailQuery.data;
  const capabilities = detail?.capabilities;
  const canManageSkill = capabilities?.edit_skill ?? false;
  const canUploadVersion = capabilities?.upload_version ?? false;
  const canManageGrants = capabilities?.manage_grants ?? false;
  const canViewFavoriteDetails = capabilities?.view_favorite_details ?? false;
  const canViewDownloadDetails = capabilities?.view_download_details ?? false;
  const canViewSensitiveDownloadDetails = capabilities?.view_sensitive_download_details ?? false;

  const initialValues = useMemo(
    () =>
      detail
        ? {
            name: detail.skill.name,
            summary: detail.skill.summary,
            description: detail.skill.description,
            category_slug: detail.skill.category_slug,
          }
        : undefined,
    [detail],
  );

  const roleOptions = (rolesQuery.data ?? [])
    .filter((item) => item.is_active)
    .map((item) => ({ label: `${item.name} (${item.code})`, value: item.id }));

  const userOptions = (usersQuery.data ?? [])
    .filter((item) => item.status === "active")
    .map((item) => ({
      label: item.primary_department
        ? `${item.display_name} (${item.username}) · ${item.primary_department.name}`
        : `${item.display_name} (${item.username})`,
      value: item.id,
    }));

  return (
    <>
      {detailQuery.isError ? <Alert type="error" showIcon message={(detailQuery.error as Error).message} /> : null}
      {detailQuery.isPending ? <Card className="content-card detail-card"><Skeleton active paragraph={{ rows: 10 }} /></Card> : null}
      {!detailQuery.isPending && !detail && !detailQuery.isError ? <Alert type="info" showIcon message="当前技能暂无可展示数据。" /> : null}

      {detail ? (
        <div id="admin-skill-detail-layout" className="detail-layout">
          <SkillOverviewSection
            categories={categoriesQuery.data ?? []}
            canManageSkill={canManageSkill}
            canUploadVersion={canUploadVersion}
            detail={detail}
            errorMessage={updateMutation.error ? (updateMutation.error as Error).message : null}
            initialValues={initialValues}
            isSaving={updateMutation.isPending}
            onOpenUpload={() => setUploadOpen(true)}
            onSubmit={(values) => updateMutation.mutate(values)}
          />

          <SkillTimelineSection recentReviews={detail.recent_reviews} versions={detail.versions} />

          <section className="detail-layout-section">
            <Row gutter={[16, 16]} className="detail-grid-row">
              <Col xs={24} xl={12} className="detail-grid-col">
                <SkillGrantsCard
                  canManageGrants={canManageGrants}
                  deleteErrorMessage={deleteGrantMutation.error ? (deleteGrantMutation.error as Error).message : null}
                  grants={grantsQuery.data ?? []}
                  isDeletingGrant={deleteGrantMutation.isPending}
                  isGrantingRoles={roleGrantMutation.isPending}
                  isGrantingUsers={userGrantMutation.isPending}
                  onDeleteGrant={(grantId, targetType) => deleteGrantMutation.mutate({ grantId, targetType })}
                  onGrantRoles={() => roleGrantMutation.mutate()}
                  onGrantUsers={() => userGrantMutation.mutate()}
                  onRoleScopeChange={setRoleScope}
                  onRoleSelectionChange={setSelectedRoleIds}
                  onUserScopeChange={setUserScope}
                  onUserSelectionChange={setSelectedUserIds}
                  roleGrantErrorMessage={roleGrantMutation.error ? (roleGrantMutation.error as Error).message : null}
                  roleOptions={roleOptions}
                  roleScope={roleScope}
                  selectedRoleIds={selectedRoleIds}
                  selectedUserIds={selectedUserIds}
                  userGrantErrorMessage={userGrantMutation.error ? (userGrantMutation.error as Error).message : null}
                  userOptions={userOptions}
                  userScope={userScope}
                />
              </Col>
              <Col xs={24} xl={12} className="detail-grid-col">
                <SkillStatsCard stats={statsQuery.data} statsWindow={statsWindow} onStatsWindowChange={setStatsWindow} />
              </Col>
            </Row>
          </section>

          <SkillEngagementRecordsSection
            canViewDownloadDetails={canViewDownloadDetails}
            canViewFavoriteDetails={canViewFavoriteDetails}
            canViewSensitiveDownloadDetails={canViewSensitiveDownloadDetails}
            downloads={downloadsQuery.data ?? []}
            favorites={favoritesQuery.data ?? []}
          />
        </div>
      ) : null}

      {canUploadVersion ? (
        <SkillUploadModal
          open={uploadOpen}
          modalId="admin-skill-detail-upload-modal"
          token={accessToken}
          onClose={() => setUploadOpen(false)}
          onSuccess={async () => {
            await queryClient.invalidateQueries({ queryKey: ["admin-skill-detail", accessToken, skillId] });
            await queryClient.invalidateQueries({ queryKey: ["admin-skill-list"] });
            message.success("新版本已上传，已进入待审核，技能详情已刷新。");
          }}
        />
      ) : null}
    </>
  );
}
