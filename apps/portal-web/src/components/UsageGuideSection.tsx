/**
 * 组件约定：
 * - 统一渲染“我是 Agent / 我是 Human”的使用指引与复制动作。
 * - 当 usage guide 缺失时展示降级文案，不允许详情区空白崩溃。
 */
import { CopyOutlined, RobotOutlined, ThunderboltOutlined, UserOutlined } from "@ant-design/icons";
import { Button, Card, Tabs, message } from "antd";

import { resolveUsageGuide } from "../lib/usageGuide";
import type { PublicSkillDetailResponse } from "../lib/portalTypes";

export function UsageGuideSection({
  detail,
  selectedUsageMode,
  setUsageMode,
}: {
  detail: PublicSkillDetailResponse;
  selectedUsageMode: "agent" | "human";
  setUsageMode: (mode: "agent" | "human") => void;
}) {
  const usageGuide = resolveUsageGuide(detail);
  const copyText = async (value: string, label: string) => {
    await navigator.clipboard.writeText(value);
    message.success(`${label}已复制`);
  };

  return (
    <Card title="安装方式" className="drawer-card">
      <Tabs
        activeKey={selectedUsageMode}
        onChange={(value) => setUsageMode(value as "agent" | "human")}
        items={[
          {
            key: "agent",
            label: (
              <span className="usage-tab-label">
                <RobotOutlined />
                我是 Agent
              </span>
            ),
            children: (
              <div className="usage-guide-grid">
                <div className="usage-guide-card">
                  <div className="usage-guide-card-head">
                    <div>
                      <strong>标准平台指引</strong>
                      <p>复制给你的 Agent，让它按平台发布版本去下载并使用这个 Skill。</p>
                    </div>
                    <Button
                      className="portal-secondary-button usage-copy-button"
                      icon={<CopyOutlined />}
                      onClick={() => copyText(usageGuide.agent.standard_prompt, "Agent 标准提示词")}
                    >
                      复制
                    </Button>
                  </div>
                  <pre className="usage-guide-code">{usageGuide.agent.standard_prompt}</pre>
                </div>
                <div className="usage-guide-card">
                  <div className="usage-guide-card-head">
                    <div>
                      <strong>优先使用平台链路</strong>
                      <p>适合希望 Agent 明确走平台下载接口、优先使用当前发布版本的场景。</p>
                    </div>
                    <Button
                      className="portal-secondary-button usage-copy-button"
                      icon={<ThunderboltOutlined />}
                      onClick={() => copyText(usageGuide.agent.accelerated_prompt, "Agent 加速提示词")}
                    >
                      复制
                    </Button>
                  </div>
                  <pre className="usage-guide-code">{usageGuide.agent.accelerated_prompt}</pre>
                </div>
              </div>
            ),
          },
          {
            key: "human",
            label: (
              <span className="usage-tab-label">
                <UserOutlined />
                我是 Human
              </span>
            ),
            children: (
              <div className="usage-guide-grid">
                <div className="usage-guide-card">
                  <div className="usage-guide-card-head">
                    <div>
                      <strong>标准下载命令</strong>
                      <p>下载当前已发布 ZIP 包并落到本地。</p>
                    </div>
                    <Button
                      className="portal-secondary-button usage-copy-button"
                      icon={<CopyOutlined />}
                      onClick={() => copyText(usageGuide.human.standard_command, "标准下载命令")}
                    >
                      复制
                    </Button>
                  </div>
                  <pre className="usage-guide-code">{usageGuide.human.standard_command}</pre>
                </div>
                <div className="usage-guide-card">
                  <div className="usage-guide-card-head">
                    <div>
                      <strong>加速下载命令</strong>
                      <p>更适合需要重试或网络不稳定时使用。</p>
                    </div>
                    <Button
                      className="portal-secondary-button usage-copy-button"
                      icon={<ThunderboltOutlined />}
                      onClick={() => copyText(usageGuide.human.accelerated_command, "加速下载命令")}
                    >
                      复制
                    </Button>
                  </div>
                  <pre className="usage-guide-code">{usageGuide.human.accelerated_command}</pre>
                </div>
                <div className="usage-guide-card">
                  <div className="usage-guide-card-head">
                    <div>
                      <strong>安装后建议操作</strong>
                      <p>下载后直接执行这段命令，解压并阅读 README。</p>
                    </div>
                    <Button
                      className="portal-secondary-button usage-copy-button"
                      icon={<CopyOutlined />}
                      onClick={() => copyText(usageGuide.human.post_install_command, "安装后命令")}
                    >
                      复制
                    </Button>
                  </div>
                  <pre className="usage-guide-code">{usageGuide.human.post_install_command}</pre>
                </div>
              </div>
            ),
          },
        ]}
      />
    </Card>
  );
}
