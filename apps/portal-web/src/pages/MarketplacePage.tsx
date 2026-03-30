import {
  Alert,
  Button,
  Card,
  Empty,
  Input,
  Pagination,
  Select,
  Space,
  Spin,
  Typography,
  Drawer,
} from "antd";
import { useDeferredValue, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  AppstoreOutlined,
  SearchOutlined,
} from "@ant-design/icons";
import dayjs from "dayjs";
import { useSearchParams } from "react-router-dom";

import { apiRequest } from "../lib/api";
import type { CategoryItem, PagedResponse, PortalUser, PublicSkillDetailResponse, PublicSkillListItem } from "../lib/portalTypes";
import { hasPermission } from "../lib/portalPermissions";
import { CategoryIcon } from "../components/CategoryIcon";
import { SkillCard } from "../components/SkillCard";
import { SkillDetailContent, SkillDetailErrorState } from "../components/SkillDetailContent";

export default function MarketplacePage({
  accessToken,
  user,
  onOpenLogin,
  onUploadEntry,
}: {
  accessToken: string | null;
  user: PortalUser | null;
  onOpenLogin: () => void;
  onUploadEntry: () => void;
}) {
  /**
   * 交互约定：
   * - 加载中：分类/列表/详情三个查询各自独立显示加载态
   * - 错误：每个查询都要展示明确错误态
   * - 空态：列表无数据时区分“有筛选条件”和“无筛选条件”
   * - 详情：通过 URLSearchParams（skill + usage）控制，保证刷新/返回行为稳定
   */
  const [searchParams, setSearchParams] = useSearchParams();
  const [category, setCategory] = useState<string | undefined>();
  const [searchInput, setSearchInput] = useState("");
  const [sort, setSort] = useState("latest");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(8);
  const deferredSearch = useDeferredValue(searchInput.trim());
  const canUpload = hasPermission(user, "skill.upload");
  const selectedSkillSlug = searchParams.get("skill");
  const selectedUsageMode = searchParams.get("usage") === "human" ? "human" : "agent";

  const categoriesQuery = useQuery({
    queryKey: ["public-categories"],
    queryFn: () => apiRequest<CategoryItem[]>("/public/categories"),
  });

  const skillsQuery = useQuery({
    queryKey: ["public-skills", category, deferredSearch, sort, page, pageSize],
    queryFn: () => {
      const query = new URLSearchParams({
        sort,
        page: String(page),
        page_size: String(pageSize),
      });
      if (category) query.set("category", category);
      if (deferredSearch) query.set("q", deferredSearch);
      return apiRequest<PagedResponse<PublicSkillListItem>>(`/public/skills?${query.toString()}`, { token: accessToken ?? undefined });
    },
  });

  const detailQuery = useQuery({
    queryKey: ["public-skill-detail", selectedSkillSlug, accessToken],
    enabled: Boolean(selectedSkillSlug),
    queryFn: () => apiRequest<PublicSkillDetailResponse>(`/public/skills/${selectedSkillSlug}`, { token: accessToken ?? undefined }),
  });

  const totalPublishedSkills = useMemo(
    () => (categoriesQuery.data ?? []).reduce((sum, item) => sum + item.skill_count, 0),
    [categoriesQuery.data],
  );
  const hasFilters = Boolean(category || deferredSearch);

  const openSkillDetail = (slug: string) => {
    const next = new URLSearchParams(searchParams);
    next.set("skill", slug);
    next.set("usage", "agent");
    setSearchParams(next, { replace: false });
  };

  const closeSkillDetail = () => {
    const next = new URLSearchParams(searchParams);
    next.delete("skill");
    next.delete("usage");
    setSearchParams(next, { replace: false });
  };

  const setUsageMode = (mode: "agent" | "human") => {
    const next = new URLSearchParams(searchParams);
    if (selectedSkillSlug) {
      next.set("skill", selectedSkillSlug);
    }
    next.set("usage", mode);
    setSearchParams(next, { replace: true });
  };

  return (
    <>
      <section className="marketplace-section" id="marketplace-section">
        <div className="marketplace-panel">
          <div className="marketplace-toolbar">
            <div className="section-heading">
              <div>
                <Typography.Text className="section-kicker">探索全部技能</Typography.Text>
                <Typography.Title level={2} className="section-title">
                创金严选-技能广场
                </Typography.Title>
              </div>
            </div>

            {categoriesQuery.isLoading ? (
              <div className="toolbar-state">
                <Spin />
              </div>
            ) : categoriesQuery.isError ? (
              <Alert type="error" showIcon message={(categoriesQuery.error as Error).message} />
            ) : (
              <div className="marketplace-toolbar-content">
                <div className="category-grid">
                  <button
                    type="button"
                    className={`category-card ${!category ? "category-card-active" : ""}`}
                    onClick={() => {
                      setCategory(undefined);
                      setPage(1);
                    }}
                  >
                    <span className="category-icon category-icon-all">
                      <AppstoreOutlined />
                    </span>
                    <span className="category-card-name">全部技能</span>
                    <strong>{totalPublishedSkills}</strong>
                  </button>
                  {(categoriesQuery.data ?? []).map((item) => (
                    <button
                      key={item.id}
                      type="button"
                      className={`category-card ${item.slug === category ? "category-card-active" : ""}`}
                      onClick={() => {
                        setCategory(item.slug);
                        setPage(1);
                      }}
                    >
                      <CategoryIcon category={{ name: item.name, slug: item.slug }} />
                      <span className="category-card-name">{item.name}</span>
                      <strong>{item.skill_count}</strong>
                    </button>
                  ))}
                </div>

                <div className="toolbar-row">
                  <Input
                    placeholder="搜索技能名称、描述或分类"
                    size="large"
                    className="toolbar-search"
                    prefix={<SearchOutlined />}
                    suffix={
                      <span className="toolbar-search-suffix" aria-hidden="true">
                        <SearchOutlined />
                      </span>
                    }
                    value={searchInput}
                    onChange={(event) => {
                      setSearchInput(event.target.value);
                      setPage(1);
                    }}
                    allowClear
                  />
                  <Select
                    size="large"
                    className="toolbar-sort"
                    value={sort}
                    onChange={(value) => {
                      setSort(value);
                      setPage(1);
                    }}
                    options={[
                      { label: "最新发布", value: "latest" },
                      { label: "下载量", value: "downloads" },
                      { label: "收藏量", value: "favorites" },
                      { label: "名称", value: "name" },
                    ]}
                  />
                </div>
              </div>
            )}
          </div>

          <div className="results-head">
            <div>
              <Typography.Text className="results-kicker">技能列表</Typography.Text>
              <Typography.Title level={3} className="results-title">
              筛选结果：{skillsQuery.data?.total ?? 0} 个技能
              </Typography.Title>
            </div>
            <Space wrap className="results-actions">
              <Button
                className="portal-secondary-button"
                onClick={() => {
                  setCategory(undefined);
                  setPage(1);
                }}
              >
                查看全部技能
              </Button>
              <Button className="portal-primary-button" type="primary" onClick={onUploadEntry}>
                {canUpload ? "上传我的技能" : user ? "进入上传通道" : "登录后上传技能"}
              </Button>
            </Space>
          </div>

          {skillsQuery.isLoading ? (
            <Card className="skill-card skill-card-wide" variant="borderless">
              <div className="center-panel">
                <Spin size="large" />
              </div>
            </Card>
          ) : skillsQuery.isError ? (
            <Card className="skill-card skill-card-wide" variant="borderless">
              <Typography.Title level={4}>技能列表加载失败</Typography.Title>
              <Typography.Paragraph className="skill-summary">{(skillsQuery.error as Error).message}</Typography.Paragraph>
            </Card>
          ) : skillsQuery.data?.items.length ? (
            <>
              <div className="skills-grid">
                {skillsQuery.data.items.map((item) => (
                  <SkillCard key={item.id} skill={item} onOpen={openSkillDetail} />
                ))}
              </div>
              <div className="pagination-row">
                <Pagination
                  current={page}
                  pageSize={pageSize}
                  total={skillsQuery.data.total}
                  onChange={(nextPage, nextSize) => {
                    setPage(nextPage);
                    setPageSize(nextSize);
                  }}
                  showSizeChanger
                  pageSizeOptions={[8, 16, 24]}
                />
              </div>
            </>
          ) : (
            <Card className="skill-card skill-card-wide" variant="borderless">
              <Empty
                description={
                  hasFilters ? (
                    <span>
                      没有找到符合条件的技能。<br />
                      试试清空筛选条件或换个关键词。
                    </span>
                  ) : (
                    <span>暂时还没有已发布技能。</span>
                  )
                }
              />
            </Card>
          )}
        </div>
      </section>

      <section className="marketplace-section" id="overview-section">
        <div className="marketplace-header marketplace-header--single">
          <div className="marketplace-panel marketplace-panel-soft">
            <div className="timeline-head">
              <Typography.Text className="section-kicker">交付流程</Typography.Text>
              <Typography.Title level={2} className="section-title">
                从投稿到发布，一站式治理
              </Typography.Title>
              <Typography.Title level={3} className="timeline-title">
                Upload → Review → Release
              </Typography.Title>
              <Typography.Paragraph className="section-copy">
                Skill Hub 将技能包的上传、审核、发布、版本与权限治理沉淀在同一条链路上，保障技能资产安全可控。规范状态机：草稿 → 待审核 → 待发布 → 已发布；审核通过后一定先进入待发布队列。
              </Typography.Paragraph>
            </div>
            <div className="timeline-grid">
              <div className="timeline-card">
                <strong>1. 上传技能包</strong>
                <p>支持前台投稿与后台上传，提交 ZIP 技能包并自动校验结构与元信息。</p>
              </div>
              <div className="timeline-card">
                <strong>2. 审核与修正</strong>
                <p>审核中心统一处理提交记录、风险项与版本变更，必要时可回退修正。</p>
              </div>
              <div className="timeline-card">
                <strong>3. 待发布队列</strong>
                <p>审核通过后进入待发布，等待运营统一发布到技能广场。</p>
              </div>
              <div className="timeline-card">
                <strong>4. 发布与数据</strong>
                <p>发布后前台可见；下载、收藏、点赞与发布数据可追溯、可统计。</p>
              </div>
            </div>
            <div className="timeline-foot">
              <Typography.Text className="timeline-foot-text">
                最近一次发布：{dayjs().format("YYYY-MM-DD")}
              </Typography.Text>
            </div>
          </div>
        </div>
      </section>

      <Drawer
        title={detailQuery.data?.skill.name ?? "技能详情"}
        placement="right"
        width={720}
        open={Boolean(selectedSkillSlug)}
        onClose={closeSkillDetail}
        className="skill-detail-drawer"
        destroyOnHidden
      >
        {detailQuery.isLoading ? (
          <div className="center-panel">
            <Spin size="large" />
          </div>
        ) : detailQuery.isError ? (
          <SkillDetailErrorState message={(detailQuery.error as Error).message} />
        ) : detailQuery.data ? (
          <SkillDetailContent
            detail={detailQuery.data}
            accessToken={accessToken}
            selectedUsageMode={selectedUsageMode}
            setUsageMode={setUsageMode}
            onOpenLogin={onOpenLogin}
          />
        ) : null}
      </Drawer>
    </>
  );
}
