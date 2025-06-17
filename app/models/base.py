"""
基础模型模块，定义所有模型的基类和共享属性。
"""
from datetime import datetime
from typing import Any

from sqlalchemy import Column, Integer, DateTime, func
from sqlalchemy.ext.declarative import declarative_base, declared_attr


class CustomBase:
    """
    自定义基类，为所有模型提供共享属性和方法。
    
    Attributes:
        id: 主键ID
        created_at: 创建时间
        updated_at: 更新时间
    """
    # 自动生成表名（类名小写）
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()
    
    # 主键
    id = Column(Integer, primary_key=True, index=True)
    
    # 时间戳
    created_at = Column(
        DateTime(timezone=True), 
        default=func.now(), 
        server_default=func.now(), 
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=func.now(),
        onupdate=func.now(),
        server_default=func.now(),
        nullable=False,
    )

    def dict(self) -> dict:
        """
        将模型转换为字典。
        
        Returns:
            dict: 模型字典表示
        """
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
    
    def __repr__(self) -> str:
        """
        模型的字符串表示。
        
        Returns:
            str: 模型字符串表示
        """
        values = {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
        return f"{self.__class__.__name__}({', '.join(f'{k}={v!r}' for k, v in values.items())})"


# 创建基类
Base = declarative_base(cls=CustomBase) 