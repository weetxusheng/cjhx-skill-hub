/** 模块约定：封装后台版本包下载流程；统一处理行级 loading、Bearer 下载和成功/失败提示，不让调用方重复拼接下载状态。 */
import { useState } from "react";
import { message } from "antd";

import { downloadBinary } from "../lib/api";

/** 后台「下载某版本 ZIP」：带 Bearer，按版本 ID 触发浏览器保存；`loadingId` 用于表格多行区分加载态。 */
export function useVersionPackageDownload(accessToken: string | null) {
  const [loadingId, setLoadingId] = useState<string | null>(null);

  const download = async (versionId: string) => {
    if (!accessToken) {
      return;
    }
    setLoadingId(versionId);
    try {
      await downloadBinary(`/admin/versions/${versionId}/package`, accessToken);
      message.success("已开始下载技能包。");
    } catch (error) {
      message.error((error as Error).message);
    } finally {
      setLoadingId(null);
    }
  };

  return { loadingId, download };
}
