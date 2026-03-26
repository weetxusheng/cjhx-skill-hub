--
-- PostgreSQL database dump
--

\restrict tEpBgmEzQUPHFneljSQVXUY3eNhxZh5cdYzXWQlSsFB2AzSpdY3OwcNsgeN93xe

-- Dumped from database version 16.13 (Homebrew)
-- Dumped by pg_dump version 16.13 (Homebrew)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

ALTER TABLE IF EXISTS ONLY public.skill_likes DROP CONSTRAINT IF EXISTS skill_likes_user_id_fkey;
ALTER TABLE IF EXISTS ONLY public.skill_likes DROP CONSTRAINT IF EXISTS skill_likes_skill_id_fkey;
ALTER TABLE IF EXISTS ONLY public.version_reviews DROP CONSTRAINT IF EXISTS fk_version_reviews_version;
ALTER TABLE IF EXISTS ONLY public.version_reviews DROP CONSTRAINT IF EXISTS fk_version_reviews_operator;
ALTER TABLE IF EXISTS ONLY public.user_roles DROP CONSTRAINT IF EXISTS fk_user_roles_user;
ALTER TABLE IF EXISTS ONLY public.user_roles DROP CONSTRAINT IF EXISTS fk_user_roles_role;
ALTER TABLE IF EXISTS ONLY public.skills DROP CONSTRAINT IF EXISTS fk_skills_owner;
ALTER TABLE IF EXISTS ONLY public.skills DROP CONSTRAINT IF EXISTS fk_skills_icon;
ALTER TABLE IF EXISTS ONLY public.skills DROP CONSTRAINT IF EXISTS fk_skills_current_published_version;
ALTER TABLE IF EXISTS ONLY public.skills DROP CONSTRAINT IF EXISTS fk_skills_category;
ALTER TABLE IF EXISTS ONLY public.skill_versions DROP CONSTRAINT IF EXISTS fk_skill_versions_skill;
ALTER TABLE IF EXISTS ONLY public.skill_versions DROP CONSTRAINT IF EXISTS fk_skill_versions_reviewed_by;
ALTER TABLE IF EXISTS ONLY public.skill_versions DROP CONSTRAINT IF EXISTS fk_skill_versions_readme;
ALTER TABLE IF EXISTS ONLY public.skill_versions DROP CONSTRAINT IF EXISTS fk_skill_versions_published_by;
ALTER TABLE IF EXISTS ONLY public.skill_versions DROP CONSTRAINT IF EXISTS fk_skill_versions_package;
ALTER TABLE IF EXISTS ONLY public.skill_versions DROP CONSTRAINT IF EXISTS fk_skill_versions_created_by;
ALTER TABLE IF EXISTS ONLY public.skill_user_grants DROP CONSTRAINT IF EXISTS fk_skill_user_grants_user;
ALTER TABLE IF EXISTS ONLY public.skill_user_grants DROP CONSTRAINT IF EXISTS fk_skill_user_grants_skill;
ALTER TABLE IF EXISTS ONLY public.skill_tags DROP CONSTRAINT IF EXISTS fk_skill_tags_tag;
ALTER TABLE IF EXISTS ONLY public.skill_tags DROP CONSTRAINT IF EXISTS fk_skill_tags_skill;
ALTER TABLE IF EXISTS ONLY public.skill_role_grants DROP CONSTRAINT IF EXISTS fk_skill_role_grants_skill;
ALTER TABLE IF EXISTS ONLY public.skill_role_grants DROP CONSTRAINT IF EXISTS fk_skill_role_grants_role;
ALTER TABLE IF EXISTS ONLY public.role_permissions DROP CONSTRAINT IF EXISTS fk_role_permissions_role;
ALTER TABLE IF EXISTS ONLY public.role_permissions DROP CONSTRAINT IF EXISTS fk_role_permissions_permission;
ALTER TABLE IF EXISTS ONLY public.refresh_tokens DROP CONSTRAINT IF EXISTS fk_refresh_tokens_user;
ALTER TABLE IF EXISTS ONLY public.file_assets DROP CONSTRAINT IF EXISTS fk_file_assets_created_by;
ALTER TABLE IF EXISTS ONLY public.favorites DROP CONSTRAINT IF EXISTS fk_favorites_user;
ALTER TABLE IF EXISTS ONLY public.favorites DROP CONSTRAINT IF EXISTS fk_favorites_skill;
ALTER TABLE IF EXISTS ONLY public.download_logs DROP CONSTRAINT IF EXISTS fk_download_logs_version;
ALTER TABLE IF EXISTS ONLY public.download_logs DROP CONSTRAINT IF EXISTS fk_download_logs_user;
ALTER TABLE IF EXISTS ONLY public.download_logs DROP CONSTRAINT IF EXISTS fk_download_logs_skill;
ALTER TABLE IF EXISTS ONLY public.audit_logs DROP CONSTRAINT IF EXISTS fk_audit_logs_actor;
DROP TRIGGER IF EXISTS trg_users_updated_at ON public.users;
DROP TRIGGER IF EXISTS trg_skills_updated_at ON public.skills;
DROP TRIGGER IF EXISTS trg_skill_versions_updated_at ON public.skill_versions;
DROP TRIGGER IF EXISTS trg_categories_updated_at ON public.categories;
DROP INDEX IF EXISTS public.uq_skill_versions_one_published;
DROP INDEX IF EXISTS public.idx_version_reviews_version_created;
DROP INDEX IF EXISTS public.idx_skills_summary_trgm;
DROP INDEX IF EXISTS public.idx_skills_published_at;
DROP INDEX IF EXISTS public.idx_skills_name_trgm;
DROP INDEX IF EXISTS public.idx_skills_favorite_count;
DROP INDEX IF EXISTS public.idx_skills_download_count;
DROP INDEX IF EXISTS public.idx_skills_category_status;
DROP INDEX IF EXISTS public.idx_skill_versions_skill_status;
DROP INDEX IF EXISTS public.idx_skill_versions_published_at;
DROP INDEX IF EXISTS public.idx_skill_user_grants_skill;
DROP INDEX IF EXISTS public.idx_skill_role_grants_skill;
DROP INDEX IF EXISTS public.idx_skill_likes_skill_created;
DROP INDEX IF EXISTS public.idx_download_logs_skill_created;
DROP INDEX IF EXISTS public.idx_categories_visible_sort;
DROP INDEX IF EXISTS public.idx_audit_logs_target;
DROP INDEX IF EXISTS public.idx_audit_logs_request_id;
ALTER TABLE IF EXISTS ONLY public.version_reviews DROP CONSTRAINT IF EXISTS version_reviews_pkey;
ALTER TABLE IF EXISTS ONLY public.users DROP CONSTRAINT IF EXISTS users_pkey;
ALTER TABLE IF EXISTS ONLY public.user_roles DROP CONSTRAINT IF EXISTS user_roles_pkey;
ALTER TABLE IF EXISTS ONLY public.users DROP CONSTRAINT IF EXISTS uq_users_username;
ALTER TABLE IF EXISTS ONLY public.users DROP CONSTRAINT IF EXISTS uq_users_email;
ALTER TABLE IF EXISTS ONLY public.tags DROP CONSTRAINT IF EXISTS uq_tags_slug;
ALTER TABLE IF EXISTS ONLY public.tags DROP CONSTRAINT IF EXISTS uq_tags_name;
ALTER TABLE IF EXISTS ONLY public.skills DROP CONSTRAINT IF EXISTS uq_skills_slug;
ALTER TABLE IF EXISTS ONLY public.skill_versions DROP CONSTRAINT IF EXISTS uq_skill_versions_skill_version;
ALTER TABLE IF EXISTS ONLY public.skill_user_grants DROP CONSTRAINT IF EXISTS uq_skill_user_grants_scope;
ALTER TABLE IF EXISTS ONLY public.skill_role_grants DROP CONSTRAINT IF EXISTS uq_skill_role_grants_scope;
ALTER TABLE IF EXISTS ONLY public.roles DROP CONSTRAINT IF EXISTS uq_roles_code;
ALTER TABLE IF EXISTS ONLY public.refresh_tokens DROP CONSTRAINT IF EXISTS uq_refresh_tokens_hash;
ALTER TABLE IF EXISTS ONLY public.permissions DROP CONSTRAINT IF EXISTS uq_permissions_code;
ALTER TABLE IF EXISTS ONLY public.file_assets DROP CONSTRAINT IF EXISTS uq_file_assets_sha256_kind;
ALTER TABLE IF EXISTS ONLY public.file_assets DROP CONSTRAINT IF EXISTS uq_file_assets_object;
ALTER TABLE IF EXISTS ONLY public.categories DROP CONSTRAINT IF EXISTS uq_categories_slug;
ALTER TABLE IF EXISTS ONLY public.categories DROP CONSTRAINT IF EXISTS uq_categories_name;
ALTER TABLE IF EXISTS ONLY public.tags DROP CONSTRAINT IF EXISTS tags_pkey;
ALTER TABLE IF EXISTS ONLY public.skills DROP CONSTRAINT IF EXISTS skills_pkey;
ALTER TABLE IF EXISTS ONLY public.skill_versions DROP CONSTRAINT IF EXISTS skill_versions_pkey;
ALTER TABLE IF EXISTS ONLY public.skill_user_grants DROP CONSTRAINT IF EXISTS skill_user_grants_pkey;
ALTER TABLE IF EXISTS ONLY public.skill_tags DROP CONSTRAINT IF EXISTS skill_tags_pkey;
ALTER TABLE IF EXISTS ONLY public.skill_role_grants DROP CONSTRAINT IF EXISTS skill_role_grants_pkey;
ALTER TABLE IF EXISTS ONLY public.roles DROP CONSTRAINT IF EXISTS roles_pkey;
ALTER TABLE IF EXISTS ONLY public.role_permissions DROP CONSTRAINT IF EXISTS role_permissions_pkey;
ALTER TABLE IF EXISTS ONLY public.refresh_tokens DROP CONSTRAINT IF EXISTS refresh_tokens_pkey;
ALTER TABLE IF EXISTS ONLY public.skill_likes DROP CONSTRAINT IF EXISTS pk_skill_likes;
ALTER TABLE IF EXISTS ONLY public.permissions DROP CONSTRAINT IF EXISTS permissions_pkey;
ALTER TABLE IF EXISTS ONLY public.file_assets DROP CONSTRAINT IF EXISTS file_assets_pkey;
ALTER TABLE IF EXISTS ONLY public.favorites DROP CONSTRAINT IF EXISTS favorites_pkey;
ALTER TABLE IF EXISTS ONLY public.download_logs DROP CONSTRAINT IF EXISTS download_logs_pkey;
ALTER TABLE IF EXISTS ONLY public.categories DROP CONSTRAINT IF EXISTS categories_pkey;
ALTER TABLE IF EXISTS ONLY public.audit_logs DROP CONSTRAINT IF EXISTS audit_logs_pkey;
ALTER TABLE IF EXISTS ONLY public.alembic_version DROP CONSTRAINT IF EXISTS alembic_version_pkc;
DROP TABLE IF EXISTS public.version_reviews;
DROP TABLE IF EXISTS public.users;
DROP TABLE IF EXISTS public.user_roles;
DROP TABLE IF EXISTS public.tags;
DROP TABLE IF EXISTS public.skills;
DROP TABLE IF EXISTS public.skill_versions;
DROP TABLE IF EXISTS public.skill_user_grants;
DROP TABLE IF EXISTS public.skill_tags;
DROP TABLE IF EXISTS public.skill_role_grants;
DROP TABLE IF EXISTS public.skill_likes;
DROP TABLE IF EXISTS public.roles;
DROP TABLE IF EXISTS public.role_permissions;
DROP TABLE IF EXISTS public.refresh_tokens;
DROP TABLE IF EXISTS public.permissions;
DROP TABLE IF EXISTS public.file_assets;
DROP TABLE IF EXISTS public.favorites;
DROP TABLE IF EXISTS public.download_logs;
DROP TABLE IF EXISTS public.categories;
DROP TABLE IF EXISTS public.audit_logs;
DROP TABLE IF EXISTS public.alembic_version;
DROP FUNCTION IF EXISTS public.set_updated_at();
DROP EXTENSION IF EXISTS pgcrypto;
DROP EXTENSION IF EXISTS pg_trgm;
--
-- Name: pg_trgm; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA public;


--
-- Name: EXTENSION pg_trgm; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION pg_trgm IS 'text similarity measurement and index searching based on trigrams';


--
-- Name: pgcrypto; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;


--
-- Name: EXTENSION pgcrypto; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION pgcrypto IS 'cryptographic functions';


--
-- Name: set_updated_at(); Type: FUNCTION; Schema: public; Owner: -
--

CREATE FUNCTION public.set_updated_at() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
        begin
          new.updated_at = now();
          return new;
        end;
        $$;


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: alembic_version; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.alembic_version (
    version_num character varying(32) NOT NULL
);


--
-- Name: audit_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.audit_logs (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    actor_user_id uuid,
    action text NOT NULL,
    target_type text NOT NULL,
    target_id uuid,
    before_json jsonb,
    after_json jsonb,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    request_id text
);


--
-- Name: categories; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.categories (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    name text NOT NULL,
    slug text NOT NULL,
    icon text,
    description text,
    sort_order integer DEFAULT 0 NOT NULL,
    is_visible boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: download_logs; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.download_logs (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    skill_id uuid NOT NULL,
    skill_version_id uuid NOT NULL,
    user_id uuid,
    ip inet,
    user_agent text,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: favorites; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.favorites (
    user_id uuid NOT NULL,
    skill_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: file_assets; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.file_assets (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    bucket text NOT NULL,
    object_key text NOT NULL,
    original_name text NOT NULL,
    mime_type text NOT NULL,
    size_bytes bigint NOT NULL,
    sha256 text NOT NULL,
    file_kind text NOT NULL,
    created_by uuid,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_file_assets_kind CHECK ((file_kind = ANY (ARRAY['package'::text, 'readme'::text, 'icon'::text, 'screenshot'::text, 'attachment'::text])))
);


--
-- Name: permissions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.permissions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    code text NOT NULL,
    name text NOT NULL,
    description text,
    group_key text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: refresh_tokens; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.refresh_tokens (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    token_hash text NOT NULL,
    expires_at timestamp with time zone NOT NULL,
    revoked_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: role_permissions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.role_permissions (
    role_id uuid NOT NULL,
    permission_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: roles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.roles (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    code text NOT NULL,
    name text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    description text,
    is_system boolean DEFAULT false NOT NULL,
    is_active boolean DEFAULT true NOT NULL
);


--
-- Name: skill_likes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.skill_likes (
    user_id uuid NOT NULL,
    skill_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: skill_role_grants; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.skill_role_grants (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    skill_id uuid NOT NULL,
    role_id uuid NOT NULL,
    permission_scope text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_skill_role_grants_scope CHECK ((permission_scope = ANY (ARRAY['owner'::text, 'maintainer'::text, 'reviewer'::text, 'publisher'::text, 'rollback'::text, 'viewer'::text])))
);


--
-- Name: skill_tags; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.skill_tags (
    skill_id uuid NOT NULL,
    tag_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: skill_user_grants; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.skill_user_grants (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    skill_id uuid NOT NULL,
    user_id uuid NOT NULL,
    permission_scope text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_skill_user_grants_scope CHECK ((permission_scope = ANY (ARRAY['owner'::text, 'maintainer'::text, 'reviewer'::text, 'publisher'::text, 'rollback'::text, 'viewer'::text])))
);


--
-- Name: skill_versions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.skill_versions (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    skill_id uuid NOT NULL,
    version text NOT NULL,
    manifest_json jsonb NOT NULL,
    changelog text DEFAULT ''::text NOT NULL,
    install_notes text DEFAULT ''::text NOT NULL,
    breaking_changes text DEFAULT ''::text NOT NULL,
    readme_markdown text NOT NULL,
    source_type text DEFAULT 'upload_zip'::text NOT NULL,
    package_file_id uuid NOT NULL,
    readme_file_id uuid,
    review_status text DEFAULT 'draft'::text NOT NULL,
    review_comment text,
    reviewed_by uuid,
    reviewed_at timestamp with time zone,
    published_by uuid,
    published_at timestamp with time zone,
    created_by uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    usage_guide_json jsonb DEFAULT '{}'::jsonb NOT NULL,
    CONSTRAINT ck_skill_versions_source CHECK ((source_type = 'upload_zip'::text)),
    CONSTRAINT ck_skill_versions_status CHECK ((review_status = ANY (ARRAY['draft'::text, 'submitted'::text, 'approved'::text, 'rejected'::text, 'published'::text, 'archived'::text])))
);


--
-- Name: skills; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.skills (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    name text NOT NULL,
    slug text NOT NULL,
    summary text NOT NULL,
    description text NOT NULL,
    owner_user_id uuid NOT NULL,
    category_id uuid NOT NULL,
    icon_file_id uuid,
    status text DEFAULT 'active'::text NOT NULL,
    current_published_version_id uuid,
    latest_version_no text,
    view_count bigint DEFAULT 0 NOT NULL,
    download_count bigint DEFAULT 0 NOT NULL,
    favorite_count bigint DEFAULT 0 NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    published_at timestamp with time zone,
    like_count bigint DEFAULT '0'::bigint NOT NULL,
    CONSTRAINT ck_skills_status CHECK ((status = ANY (ARRAY['active'::text, 'inactive'::text])))
);


--
-- Name: tags; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.tags (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    name text NOT NULL,
    slug text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: user_roles; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.user_roles (
    user_id uuid NOT NULL,
    role_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    username text NOT NULL,
    password_hash text NOT NULL,
    display_name text NOT NULL,
    email text,
    status text DEFAULT 'active'::text NOT NULL,
    last_login_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_users_status CHECK ((status = ANY (ARRAY['active'::text, 'disabled'::text])))
);


--
-- Name: version_reviews; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.version_reviews (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    skill_version_id uuid NOT NULL,
    action text NOT NULL,
    comment text DEFAULT ''::text NOT NULL,
    operator_user_id uuid NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT ck_version_reviews_action CHECK ((action = ANY (ARRAY['submit'::text, 'approve'::text, 'reject'::text, 'publish'::text, 'archive'::text, 'rollback_publish'::text])))
);


--
-- Data for Name: alembic_version; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.alembic_version (version_num) FROM stdin;
0014_expand_skill_grant_scopes
\.


--
-- Data for Name: audit_logs; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.audit_logs (id, actor_user_id, action, target_type, target_id, before_json, after_json, created_at, request_id) FROM stdin;
\.


--
-- Data for Name: categories; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.categories (id, name, slug, icon, description, sort_order, is_visible, created_at, updated_at) FROM stdin;
dcc5eaad-8ede-4ab0-95e3-9e325b2829d6	AI 智能	ai-intelligence	SparkleOutlined	智能体、模型与推理增强类技能	10	t	2026-03-26 10:24:33.117383+08	2026-03-26 10:24:33.117383+08
ff2cd8ee-c8ac-4410-b6b8-b62973cd5dd2	开发工具	developer-tools	CodeOutlined	开发、调试、构建与代码协作技能	20	t	2026-03-26 10:24:33.117383+08	2026-03-26 10:24:33.117383+08
7740451b-9d55-4795-b2e2-ba0a00bf773d	效率提升	productivity	ThunderboltOutlined	办公、自动化、效率优化技能	30	t	2026-03-26 10:24:33.117383+08	2026-03-26 10:24:33.117383+08
90ec247c-5b71-4f82-a390-13c7180362b3	数据分析	data-analysis	BarChartOutlined	数据处理、报表、可视化技能	40	t	2026-03-26 10:24:33.117383+08	2026-03-26 10:24:33.117383+08
530efb52-3f5a-4dcb-b8c1-144cc01badb3	内容创作	content-creation	EditOutlined	文本、图片、音视频创作技能	50	t	2026-03-26 10:24:33.117383+08	2026-03-26 10:24:33.117383+08
00ef9604-d86f-4102-a7f1-b94a59bb60eb	安全合规	security-compliance	SafetyCertificateOutlined	安全扫描、审计、合规检查技能	60	t	2026-03-26 10:24:33.117383+08	2026-03-26 10:24:33.117383+08
4d40844a-a1e1-4da2-8849-80fc3efcd3c1	通讯协作	communication-collaboration	TeamOutlined	IM、协同、邮件与知识流转技能	70	t	2026-03-26 10:24:33.117383+08	2026-03-26 10:24:33.117383+08
\.


--
-- Data for Name: download_logs; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.download_logs (id, skill_id, skill_version_id, user_id, ip, user_agent, created_at) FROM stdin;
\.


--
-- Data for Name: favorites; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.favorites (user_id, skill_id, created_at) FROM stdin;
\.


--
-- Data for Name: file_assets; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.file_assets (id, bucket, object_key, original_name, mime_type, size_bytes, sha256, file_kind, created_by, created_at) FROM stdin;
\.


--
-- Data for Name: permissions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.permissions (id, code, name, description, group_key, created_at) FROM stdin;
6f800cda-8d9f-4aeb-b66e-2874149532e6	skill.view	查看技能	查看后台技能列表、技能详情和版本详情	skill	2026-03-26 10:24:33.117383+08
9d73e88a-ea22-4b4f-b0c5-1830ff7276d0	skill.upload	上传技能	上传新技能包或追加新版本	skill	2026-03-26 10:24:33.117383+08
0f02b9e8-97a7-48cc-a65d-2703bdd32101	skill.edit	编辑技能主档	编辑技能主档展示信息	skill	2026-03-26 10:24:33.117383+08
ac56ab5d-9f0a-4de9-a175-c59f839b1a41	skill.version.edit	编辑版本文案	编辑 draft/rejected 版本文案与使用指引	skill	2026-03-26 10:24:33.117383+08
067a4c7d-0d1b-45e4-ab2b-5352e6a670a7	skill.submit	提交审核	将 draft/rejected 版本提交审核	skill	2026-03-26 10:24:33.117383+08
d5f8c772-3543-4179-b17b-03559dcea3f2	skill.review	审核技能	查看待审队列并执行通过/拒绝	skill	2026-03-26 10:24:33.117383+08
23ba79d1-286e-493d-95e9-730e253a4a2e	skill.publish	发布技能	发布 approved 版本	skill	2026-03-26 10:24:33.117383+08
dbde562c-2bfc-47b3-ae8c-430578e7efaf	skill.archive	归档技能	归档当前 published 版本	skill	2026-03-26 10:24:33.117383+08
b8f033e3-0439-467b-b362-b2e4322a3622	skill.rollback	回滚技能	回滚到历史 archived 版本	skill	2026-03-26 10:24:33.117383+08
b2dd087e-8280-429a-a8da-62c254bfc145	admin.dashboard.view	查看仪表盘	访问后台 Dashboard	admin	2026-03-26 10:24:33.117383+08
b1722e51-f2bf-465b-93a7-3b7c9b4bf373	admin.categories.view	查看分类管理	查看后台分类列表	admin	2026-03-26 10:24:33.117383+08
884054a0-a4fd-4ada-a2aa-3820d2e655a4	admin.categories.manage	管理分类	新建、编辑、删除分类	admin	2026-03-26 10:24:33.117383+08
c2a30494-2fd8-468b-9655-b94a3a651d5b	admin.users.view	查看用户管理	查看后台用户列表	admin	2026-03-26 10:24:33.117383+08
b92d29e9-7645-458d-9495-8b997b12bf59	admin.users.manage	管理用户	配置用户角色、启停用用户	admin	2026-03-26 10:24:33.117383+08
81127f4c-e036-48af-ac92-df4402fc70f5	admin.roles.view	查看角色管理	查看角色和权限配置	admin	2026-03-26 10:24:33.117383+08
4412d323-d2f8-4275-b967-f6c8186cd60e	admin.roles.manage	管理角色	创建、编辑、启停用角色并配置权限	admin	2026-03-26 10:24:33.117383+08
96540acc-e793-4fdd-8c4f-6fddb7a85eb5	admin.audit.view	查看审计日志	查看后台审计日志	admin	2026-03-26 10:24:33.117383+08
0514be9f-950a-4cb7-ac17-bb8e6ace845f	admin.audit.export	导出审计日志	导出后台审计日志	admin	2026-03-26 10:24:33.117383+08
\.


--
-- Data for Name: refresh_tokens; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.refresh_tokens (id, user_id, token_hash, expires_at, revoked_at, created_at) FROM stdin;
\.


--
-- Data for Name: role_permissions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.role_permissions (role_id, permission_id, created_at) FROM stdin;
cc162c2f-d913-45e3-bdbb-fe9f5d15c9f4	b2dd087e-8280-429a-a8da-62c254bfc145	2026-03-26 10:24:33.117383+08
cc162c2f-d913-45e3-bdbb-fe9f5d15c9f4	b1722e51-f2bf-465b-93a7-3b7c9b4bf373	2026-03-26 10:24:33.117383+08
cc162c2f-d913-45e3-bdbb-fe9f5d15c9f4	6f800cda-8d9f-4aeb-b66e-2874149532e6	2026-03-26 10:24:33.117383+08
cc162c2f-d913-45e3-bdbb-fe9f5d15c9f4	9d73e88a-ea22-4b4f-b0c5-1830ff7276d0	2026-03-26 10:24:33.117383+08
cc162c2f-d913-45e3-bdbb-fe9f5d15c9f4	0f02b9e8-97a7-48cc-a65d-2703bdd32101	2026-03-26 10:24:33.117383+08
cc162c2f-d913-45e3-bdbb-fe9f5d15c9f4	ac56ab5d-9f0a-4de9-a175-c59f839b1a41	2026-03-26 10:24:33.117383+08
cc162c2f-d913-45e3-bdbb-fe9f5d15c9f4	067a4c7d-0d1b-45e4-ab2b-5352e6a670a7	2026-03-26 10:24:33.117383+08
a1623d52-29f8-4efb-b379-8026e4ec092e	b2dd087e-8280-429a-a8da-62c254bfc145	2026-03-26 10:24:33.117383+08
a1623d52-29f8-4efb-b379-8026e4ec092e	b1722e51-f2bf-465b-93a7-3b7c9b4bf373	2026-03-26 10:24:33.117383+08
a1623d52-29f8-4efb-b379-8026e4ec092e	6f800cda-8d9f-4aeb-b66e-2874149532e6	2026-03-26 10:24:33.117383+08
a1623d52-29f8-4efb-b379-8026e4ec092e	d5f8c772-3543-4179-b17b-03559dcea3f2	2026-03-26 10:24:33.117383+08
c1945ec3-320d-4e2d-94b0-166db5678b56	b2dd087e-8280-429a-a8da-62c254bfc145	2026-03-26 10:24:33.117383+08
c1945ec3-320d-4e2d-94b0-166db5678b56	b1722e51-f2bf-465b-93a7-3b7c9b4bf373	2026-03-26 10:24:33.117383+08
c1945ec3-320d-4e2d-94b0-166db5678b56	6f800cda-8d9f-4aeb-b66e-2874149532e6	2026-03-26 10:24:33.117383+08
c1945ec3-320d-4e2d-94b0-166db5678b56	23ba79d1-286e-493d-95e9-730e253a4a2e	2026-03-26 10:24:33.117383+08
c1945ec3-320d-4e2d-94b0-166db5678b56	dbde562c-2bfc-47b3-ae8c-430578e7efaf	2026-03-26 10:24:33.117383+08
c1945ec3-320d-4e2d-94b0-166db5678b56	b8f033e3-0439-467b-b362-b2e4322a3622	2026-03-26 10:24:33.117383+08
97e0593c-7f60-4b1d-a815-1321bdbf6108	6f800cda-8d9f-4aeb-b66e-2874149532e6	2026-03-26 10:24:33.117383+08
97e0593c-7f60-4b1d-a815-1321bdbf6108	9d73e88a-ea22-4b4f-b0c5-1830ff7276d0	2026-03-26 10:24:33.117383+08
97e0593c-7f60-4b1d-a815-1321bdbf6108	0f02b9e8-97a7-48cc-a65d-2703bdd32101	2026-03-26 10:24:33.117383+08
97e0593c-7f60-4b1d-a815-1321bdbf6108	ac56ab5d-9f0a-4de9-a175-c59f839b1a41	2026-03-26 10:24:33.117383+08
97e0593c-7f60-4b1d-a815-1321bdbf6108	067a4c7d-0d1b-45e4-ab2b-5352e6a670a7	2026-03-26 10:24:33.117383+08
97e0593c-7f60-4b1d-a815-1321bdbf6108	d5f8c772-3543-4179-b17b-03559dcea3f2	2026-03-26 10:24:33.117383+08
97e0593c-7f60-4b1d-a815-1321bdbf6108	23ba79d1-286e-493d-95e9-730e253a4a2e	2026-03-26 10:24:33.117383+08
97e0593c-7f60-4b1d-a815-1321bdbf6108	dbde562c-2bfc-47b3-ae8c-430578e7efaf	2026-03-26 10:24:33.117383+08
97e0593c-7f60-4b1d-a815-1321bdbf6108	b8f033e3-0439-467b-b362-b2e4322a3622	2026-03-26 10:24:33.117383+08
97e0593c-7f60-4b1d-a815-1321bdbf6108	b2dd087e-8280-429a-a8da-62c254bfc145	2026-03-26 10:24:33.117383+08
97e0593c-7f60-4b1d-a815-1321bdbf6108	b1722e51-f2bf-465b-93a7-3b7c9b4bf373	2026-03-26 10:24:33.117383+08
97e0593c-7f60-4b1d-a815-1321bdbf6108	884054a0-a4fd-4ada-a2aa-3820d2e655a4	2026-03-26 10:24:33.117383+08
97e0593c-7f60-4b1d-a815-1321bdbf6108	c2a30494-2fd8-468b-9655-b94a3a651d5b	2026-03-26 10:24:33.117383+08
97e0593c-7f60-4b1d-a815-1321bdbf6108	b92d29e9-7645-458d-9495-8b997b12bf59	2026-03-26 10:24:33.117383+08
97e0593c-7f60-4b1d-a815-1321bdbf6108	81127f4c-e036-48af-ac92-df4402fc70f5	2026-03-26 10:24:33.117383+08
97e0593c-7f60-4b1d-a815-1321bdbf6108	4412d323-d2f8-4275-b967-f6c8186cd60e	2026-03-26 10:24:33.117383+08
97e0593c-7f60-4b1d-a815-1321bdbf6108	96540acc-e793-4fdd-8c4f-6fddb7a85eb5	2026-03-26 10:24:33.117383+08
97e0593c-7f60-4b1d-a815-1321bdbf6108	0514be9f-950a-4cb7-ac17-bb8e6ace845f	2026-03-26 10:24:33.117383+08
\.


--
-- Data for Name: roles; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.roles (id, code, name, created_at, description, is_system, is_active) FROM stdin;
c7b996e9-4e92-4faf-9168-a8984f10e5be	viewer	浏览者	2026-03-26 10:24:33.117383+08	仅浏览前台技能广场	t	t
cc162c2f-d913-45e3-bdbb-fe9f5d15c9f4	contributor	贡献者	2026-03-26 10:24:33.117383+08	可上传、编辑并提交技能版本	t	t
a1623d52-29f8-4efb-b379-8026e4ec092e	reviewer	审核员	2026-03-26 10:24:33.117383+08	可审核待审技能版本	t	t
c1945ec3-320d-4e2d-94b0-166db5678b56	publisher	发布员	2026-03-26 10:24:33.117383+08	可发布、归档与回滚技能版本	t	t
97e0593c-7f60-4b1d-a815-1321bdbf6108	admin	管理员	2026-03-26 10:24:33.117383+08	拥有后台全部治理权限	t	t
\.


--
-- Data for Name: skill_likes; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.skill_likes (user_id, skill_id, created_at) FROM stdin;
\.


--
-- Data for Name: skill_role_grants; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.skill_role_grants (id, skill_id, role_id, permission_scope, created_at) FROM stdin;
\.


--
-- Data for Name: skill_tags; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.skill_tags (skill_id, tag_id, created_at) FROM stdin;
\.


--
-- Data for Name: skill_user_grants; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.skill_user_grants (id, skill_id, user_id, permission_scope, created_at) FROM stdin;
\.


--
-- Data for Name: skill_versions; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.skill_versions (id, skill_id, version, manifest_json, changelog, install_notes, breaking_changes, readme_markdown, source_type, package_file_id, readme_file_id, review_status, review_comment, reviewed_by, reviewed_at, published_by, published_at, created_by, created_at, updated_at, usage_guide_json) FROM stdin;
\.


--
-- Data for Name: skills; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.skills (id, name, slug, summary, description, owner_user_id, category_id, icon_file_id, status, current_published_version_id, latest_version_no, view_count, download_count, favorite_count, created_at, updated_at, published_at, like_count) FROM stdin;
\.


--
-- Data for Name: tags; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.tags (id, name, slug, created_at) FROM stdin;
\.


--
-- Data for Name: user_roles; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.user_roles (user_id, role_id, created_at) FROM stdin;
0c69ff37-ac3c-4891-a10c-b91f82d7ecc4	97e0593c-7f60-4b1d-a815-1321bdbf6108	2026-03-26 10:24:33.117383+08
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.users (id, username, password_hash, display_name, email, status, last_login_at, created_at, updated_at) FROM stdin;
0c69ff37-ac3c-4891-a10c-b91f82d7ecc4	admin	$argon2id$v=19$m=65536,t=3,p=4$ooyYs8u8uUZfcG0i00Eewg$nI6bRfZxU6wg9uRVlzk9G5EYBqIwxOBcYSmZWbC3jPo	System Admin	admin@skillhub.local	active	\N	2026-03-26 10:24:33.117383+08	2026-03-26 10:24:33.117383+08
\.


--
-- Data for Name: version_reviews; Type: TABLE DATA; Schema: public; Owner: -
--

COPY public.version_reviews (id, skill_version_id, action, comment, operator_user_id, created_at) FROM stdin;
\.


--
-- Name: alembic_version alembic_version_pkc; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.alembic_version
    ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num);


--
-- Name: audit_logs audit_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT audit_logs_pkey PRIMARY KEY (id);


--
-- Name: categories categories_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.categories
    ADD CONSTRAINT categories_pkey PRIMARY KEY (id);


--
-- Name: download_logs download_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.download_logs
    ADD CONSTRAINT download_logs_pkey PRIMARY KEY (id);


--
-- Name: favorites favorites_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.favorites
    ADD CONSTRAINT favorites_pkey PRIMARY KEY (user_id, skill_id);


--
-- Name: file_assets file_assets_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.file_assets
    ADD CONSTRAINT file_assets_pkey PRIMARY KEY (id);


--
-- Name: permissions permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permissions
    ADD CONSTRAINT permissions_pkey PRIMARY KEY (id);


--
-- Name: skill_likes pk_skill_likes; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.skill_likes
    ADD CONSTRAINT pk_skill_likes PRIMARY KEY (user_id, skill_id);


--
-- Name: refresh_tokens refresh_tokens_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.refresh_tokens
    ADD CONSTRAINT refresh_tokens_pkey PRIMARY KEY (id);


--
-- Name: role_permissions role_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT role_permissions_pkey PRIMARY KEY (role_id, permission_id);


--
-- Name: roles roles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_pkey PRIMARY KEY (id);


--
-- Name: skill_role_grants skill_role_grants_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.skill_role_grants
    ADD CONSTRAINT skill_role_grants_pkey PRIMARY KEY (id);


--
-- Name: skill_tags skill_tags_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.skill_tags
    ADD CONSTRAINT skill_tags_pkey PRIMARY KEY (skill_id, tag_id);


--
-- Name: skill_user_grants skill_user_grants_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.skill_user_grants
    ADD CONSTRAINT skill_user_grants_pkey PRIMARY KEY (id);


--
-- Name: skill_versions skill_versions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.skill_versions
    ADD CONSTRAINT skill_versions_pkey PRIMARY KEY (id);


--
-- Name: skills skills_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.skills
    ADD CONSTRAINT skills_pkey PRIMARY KEY (id);


--
-- Name: tags tags_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tags
    ADD CONSTRAINT tags_pkey PRIMARY KEY (id);


--
-- Name: categories uq_categories_name; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.categories
    ADD CONSTRAINT uq_categories_name UNIQUE (name);


--
-- Name: categories uq_categories_slug; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.categories
    ADD CONSTRAINT uq_categories_slug UNIQUE (slug);


--
-- Name: file_assets uq_file_assets_object; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.file_assets
    ADD CONSTRAINT uq_file_assets_object UNIQUE (bucket, object_key);


--
-- Name: file_assets uq_file_assets_sha256_kind; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.file_assets
    ADD CONSTRAINT uq_file_assets_sha256_kind UNIQUE (sha256, file_kind);


--
-- Name: permissions uq_permissions_code; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.permissions
    ADD CONSTRAINT uq_permissions_code UNIQUE (code);


--
-- Name: refresh_tokens uq_refresh_tokens_hash; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.refresh_tokens
    ADD CONSTRAINT uq_refresh_tokens_hash UNIQUE (token_hash);


--
-- Name: roles uq_roles_code; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT uq_roles_code UNIQUE (code);


--
-- Name: skill_role_grants uq_skill_role_grants_scope; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.skill_role_grants
    ADD CONSTRAINT uq_skill_role_grants_scope UNIQUE (skill_id, role_id, permission_scope);


--
-- Name: skill_user_grants uq_skill_user_grants_scope; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.skill_user_grants
    ADD CONSTRAINT uq_skill_user_grants_scope UNIQUE (skill_id, user_id, permission_scope);


--
-- Name: skill_versions uq_skill_versions_skill_version; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.skill_versions
    ADD CONSTRAINT uq_skill_versions_skill_version UNIQUE (skill_id, version);


--
-- Name: skills uq_skills_slug; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.skills
    ADD CONSTRAINT uq_skills_slug UNIQUE (slug);


--
-- Name: tags uq_tags_name; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tags
    ADD CONSTRAINT uq_tags_name UNIQUE (name);


--
-- Name: tags uq_tags_slug; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.tags
    ADD CONSTRAINT uq_tags_slug UNIQUE (slug);


--
-- Name: users uq_users_email; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT uq_users_email UNIQUE (email);


--
-- Name: users uq_users_username; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT uq_users_username UNIQUE (username);


--
-- Name: user_roles user_roles_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT user_roles_pkey PRIMARY KEY (user_id, role_id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: version_reviews version_reviews_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.version_reviews
    ADD CONSTRAINT version_reviews_pkey PRIMARY KEY (id);


--
-- Name: idx_audit_logs_request_id; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_logs_request_id ON public.audit_logs USING btree (request_id);


--
-- Name: idx_audit_logs_target; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_audit_logs_target ON public.audit_logs USING btree (target_type, target_id, created_at);


--
-- Name: idx_categories_visible_sort; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_categories_visible_sort ON public.categories USING btree (is_visible, sort_order);


--
-- Name: idx_download_logs_skill_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_download_logs_skill_created ON public.download_logs USING btree (skill_id, created_at);


--
-- Name: idx_skill_likes_skill_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_skill_likes_skill_created ON public.skill_likes USING btree (skill_id, created_at);


--
-- Name: idx_skill_role_grants_skill; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_skill_role_grants_skill ON public.skill_role_grants USING btree (skill_id);


--
-- Name: idx_skill_user_grants_skill; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_skill_user_grants_skill ON public.skill_user_grants USING btree (skill_id);


--
-- Name: idx_skill_versions_published_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_skill_versions_published_at ON public.skill_versions USING btree (published_at);


--
-- Name: idx_skill_versions_skill_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_skill_versions_skill_status ON public.skill_versions USING btree (skill_id, review_status);


--
-- Name: idx_skills_category_status; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_skills_category_status ON public.skills USING btree (category_id, status);


--
-- Name: idx_skills_download_count; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_skills_download_count ON public.skills USING btree (download_count);


--
-- Name: idx_skills_favorite_count; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_skills_favorite_count ON public.skills USING btree (favorite_count);


--
-- Name: idx_skills_name_trgm; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_skills_name_trgm ON public.skills USING gin (name public.gin_trgm_ops);


--
-- Name: idx_skills_published_at; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_skills_published_at ON public.skills USING btree (published_at);


--
-- Name: idx_skills_summary_trgm; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_skills_summary_trgm ON public.skills USING gin (summary public.gin_trgm_ops);


--
-- Name: idx_version_reviews_version_created; Type: INDEX; Schema: public; Owner: -
--

CREATE INDEX idx_version_reviews_version_created ON public.version_reviews USING btree (skill_version_id, created_at);


--
-- Name: uq_skill_versions_one_published; Type: INDEX; Schema: public; Owner: -
--

CREATE UNIQUE INDEX uq_skill_versions_one_published ON public.skill_versions USING btree (skill_id) WHERE (review_status = 'published'::text);


--
-- Name: categories trg_categories_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_categories_updated_at BEFORE UPDATE ON public.categories FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


--
-- Name: skill_versions trg_skill_versions_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_skill_versions_updated_at BEFORE UPDATE ON public.skill_versions FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


--
-- Name: skills trg_skills_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_skills_updated_at BEFORE UPDATE ON public.skills FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


--
-- Name: users trg_users_updated_at; Type: TRIGGER; Schema: public; Owner: -
--

CREATE TRIGGER trg_users_updated_at BEFORE UPDATE ON public.users FOR EACH ROW EXECUTE FUNCTION public.set_updated_at();


--
-- Name: audit_logs fk_audit_logs_actor; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.audit_logs
    ADD CONSTRAINT fk_audit_logs_actor FOREIGN KEY (actor_user_id) REFERENCES public.users(id);


--
-- Name: download_logs fk_download_logs_skill; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.download_logs
    ADD CONSTRAINT fk_download_logs_skill FOREIGN KEY (skill_id) REFERENCES public.skills(id);


--
-- Name: download_logs fk_download_logs_user; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.download_logs
    ADD CONSTRAINT fk_download_logs_user FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: download_logs fk_download_logs_version; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.download_logs
    ADD CONSTRAINT fk_download_logs_version FOREIGN KEY (skill_version_id) REFERENCES public.skill_versions(id);


--
-- Name: favorites fk_favorites_skill; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.favorites
    ADD CONSTRAINT fk_favorites_skill FOREIGN KEY (skill_id) REFERENCES public.skills(id) ON DELETE CASCADE;


--
-- Name: favorites fk_favorites_user; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.favorites
    ADD CONSTRAINT fk_favorites_user FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: file_assets fk_file_assets_created_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.file_assets
    ADD CONSTRAINT fk_file_assets_created_by FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: refresh_tokens fk_refresh_tokens_user; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.refresh_tokens
    ADD CONSTRAINT fk_refresh_tokens_user FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: role_permissions fk_role_permissions_permission; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT fk_role_permissions_permission FOREIGN KEY (permission_id) REFERENCES public.permissions(id) ON DELETE CASCADE;


--
-- Name: role_permissions fk_role_permissions_role; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.role_permissions
    ADD CONSTRAINT fk_role_permissions_role FOREIGN KEY (role_id) REFERENCES public.roles(id) ON DELETE CASCADE;


--
-- Name: skill_role_grants fk_skill_role_grants_role; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.skill_role_grants
    ADD CONSTRAINT fk_skill_role_grants_role FOREIGN KEY (role_id) REFERENCES public.roles(id) ON DELETE CASCADE;


--
-- Name: skill_role_grants fk_skill_role_grants_skill; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.skill_role_grants
    ADD CONSTRAINT fk_skill_role_grants_skill FOREIGN KEY (skill_id) REFERENCES public.skills(id) ON DELETE CASCADE;


--
-- Name: skill_tags fk_skill_tags_skill; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.skill_tags
    ADD CONSTRAINT fk_skill_tags_skill FOREIGN KEY (skill_id) REFERENCES public.skills(id) ON DELETE CASCADE;


--
-- Name: skill_tags fk_skill_tags_tag; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.skill_tags
    ADD CONSTRAINT fk_skill_tags_tag FOREIGN KEY (tag_id) REFERENCES public.tags(id) ON DELETE CASCADE;


--
-- Name: skill_user_grants fk_skill_user_grants_skill; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.skill_user_grants
    ADD CONSTRAINT fk_skill_user_grants_skill FOREIGN KEY (skill_id) REFERENCES public.skills(id) ON DELETE CASCADE;


--
-- Name: skill_user_grants fk_skill_user_grants_user; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.skill_user_grants
    ADD CONSTRAINT fk_skill_user_grants_user FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: skill_versions fk_skill_versions_created_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.skill_versions
    ADD CONSTRAINT fk_skill_versions_created_by FOREIGN KEY (created_by) REFERENCES public.users(id);


--
-- Name: skill_versions fk_skill_versions_package; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.skill_versions
    ADD CONSTRAINT fk_skill_versions_package FOREIGN KEY (package_file_id) REFERENCES public.file_assets(id);


--
-- Name: skill_versions fk_skill_versions_published_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.skill_versions
    ADD CONSTRAINT fk_skill_versions_published_by FOREIGN KEY (published_by) REFERENCES public.users(id);


--
-- Name: skill_versions fk_skill_versions_readme; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.skill_versions
    ADD CONSTRAINT fk_skill_versions_readme FOREIGN KEY (readme_file_id) REFERENCES public.file_assets(id);


--
-- Name: skill_versions fk_skill_versions_reviewed_by; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.skill_versions
    ADD CONSTRAINT fk_skill_versions_reviewed_by FOREIGN KEY (reviewed_by) REFERENCES public.users(id);


--
-- Name: skill_versions fk_skill_versions_skill; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.skill_versions
    ADD CONSTRAINT fk_skill_versions_skill FOREIGN KEY (skill_id) REFERENCES public.skills(id) ON DELETE CASCADE;


--
-- Name: skills fk_skills_category; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.skills
    ADD CONSTRAINT fk_skills_category FOREIGN KEY (category_id) REFERENCES public.categories(id);


--
-- Name: skills fk_skills_current_published_version; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.skills
    ADD CONSTRAINT fk_skills_current_published_version FOREIGN KEY (current_published_version_id) REFERENCES public.skill_versions(id);


--
-- Name: skills fk_skills_icon; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.skills
    ADD CONSTRAINT fk_skills_icon FOREIGN KEY (icon_file_id) REFERENCES public.file_assets(id);


--
-- Name: skills fk_skills_owner; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.skills
    ADD CONSTRAINT fk_skills_owner FOREIGN KEY (owner_user_id) REFERENCES public.users(id);


--
-- Name: user_roles fk_user_roles_role; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT fk_user_roles_role FOREIGN KEY (role_id) REFERENCES public.roles(id) ON DELETE CASCADE;


--
-- Name: user_roles fk_user_roles_user; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.user_roles
    ADD CONSTRAINT fk_user_roles_user FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: version_reviews fk_version_reviews_operator; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.version_reviews
    ADD CONSTRAINT fk_version_reviews_operator FOREIGN KEY (operator_user_id) REFERENCES public.users(id);


--
-- Name: version_reviews fk_version_reviews_version; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.version_reviews
    ADD CONSTRAINT fk_version_reviews_version FOREIGN KEY (skill_version_id) REFERENCES public.skill_versions(id) ON DELETE CASCADE;


--
-- Name: skill_likes skill_likes_skill_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.skill_likes
    ADD CONSTRAINT skill_likes_skill_id_fkey FOREIGN KEY (skill_id) REFERENCES public.skills(id) ON DELETE CASCADE;


--
-- Name: skill_likes skill_likes_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.skill_likes
    ADD CONSTRAINT skill_likes_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict tEpBgmEzQUPHFneljSQVXUY3eNhxZh5cdYzXWQlSsFB2AzSpdY3OwcNsgeN93xe

