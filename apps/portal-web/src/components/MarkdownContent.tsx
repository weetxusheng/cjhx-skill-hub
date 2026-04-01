/**
 * 组件约定：
 * - 统一渲染门户 Markdown 内容，避免各页面直接操作 HTML 字符串。
 * - 默认开启 GFM 常见语法支持，不解析原始 HTML，降低格式和安全差异。
 * - 样式统一限定在 `.portal-markdown-content` 根类名下，避免影响项目其他正文区域。
 */
import type { Components } from "react-markdown";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import styles from "./MarkdownContent.module.css";

const markdownComponents: Components = {
  a: ({ node: _node, href, ...props }) => (
    <a href={href} target="_blank" rel="noreferrer noopener" {...props} />
  ),
  table: ({ node: _node, ...props }) => (
    <div className={styles.tableWrap}>
      <table {...props} />
    </div>
  ),
};

export function MarkdownContent({ markdown }: { markdown: string }) {
  return (
    <div className={styles.root}>
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
        {markdown}
      </ReactMarkdown>
    </div>
  );
}
