"""SQLAlchemy 声明式基类，所有 ORM 模型均继承此类。"""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """ORM 模型基类。"""

    pass
