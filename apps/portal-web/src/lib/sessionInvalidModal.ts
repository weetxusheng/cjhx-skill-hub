/** 模块约定：统一前台登录失效提示；并发请求失效时只保留一个提示弹窗，避免用户在技能广场被重复打断。 */
import { Modal } from "antd";

let open = false;

/** 在 access/refresh 均无法继续时提示用户从 OA 重新进入技能广场（避免并发请求重复弹窗）。 */
export function showSessionInvalidModal(): void {
  if (open || typeof window === "undefined") {
    return;
  }
  open = true;
  Modal.warning({
    title: "登录已失效",
    content:
      "当前登录状态无法自动恢复。请关闭本页面，回到 OA 首页后重新点击「技能广场」进入。",
    okText: "我知道了",
    onOk: () => {
      open = false;
    },
    onCancel: () => {
      open = false;
    },
  });
}
