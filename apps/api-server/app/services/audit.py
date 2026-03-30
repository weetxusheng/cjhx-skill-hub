from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.request_context import get_request_id
from app.models.audit_log import AuditLog

# 审计日志写入辅助模块。
#
# 约束：
# - 任何会改变业务状态的后端写操作都必须写入 `audit_logs`。
# - 每条审计记录都通过 `request_id` 关联到当前请求。
#
# 参考：docs/10-architecture/data-and-permissions.md


def write_audit_log(
    db: Session,
    *,
    actor_user_id: UUID | None,
    action: str,
    target_type: str,
    target_id: UUID | None,
    before_json: dict | None = None,
    after_json: dict | None = None,
) -> None:
    """向当前数据库会话追加一条审计日志记录。

    参数:
    - db: SQLAlchemy 会话，调用方负责 commit/rollback。
    - actor_user_id: 操作者用户 ID；系统级或匿名场景可为 None。
    - action: 审计动作名，建议采用 `domain.entity.action` 风格。
    - target_type: 目标实体类型（如 skill、skill_version）。
    - target_id: 目标实体主键；无实体时可为 None。
    - before_json: 变更前快照（仅必要字段）。
    - after_json: 变更后快照（仅必要字段）。

    副作用:
    - 仅执行 `db.add`，不提交事务；`request_id` 从当前请求上下文注入。

    注意:
    - 禁止在审计字段中写入敏感凭据或大体积正文。
    """
    db.add(
        AuditLog(
            actor_user_id=actor_user_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            request_id=get_request_id(),
            before_json=before_json,
            after_json=after_json,
        )
    )
