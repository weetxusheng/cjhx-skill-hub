/** 模块约定：统一后台登录失效时的提示弹窗；同一轮失效请求只弹一次，避免并发 401 造成重复打断。 */
import { Modal } from "antd";

let open = false;

/** 在 access/refresh 均无法继续时提示用户重新进入（避免并发请求重复弹窗）。 */
export function showSessionInvalidModal(): void {
  if (open || typeof window === "undefined") {
    return;
  }
  open = true;
  Modal.warning({
    title: "登录已失效",
    content:
      "当前登录状态无法自动恢复。请关闭本页签后重新登录，或从 OA 首页再次进入管理后台。",
    okText: "我知道了",
    onOk: () => {
      open = false;
    },
    onCancel: () => {
      open = false;
    },
  });
}
