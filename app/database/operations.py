"""
数据库操作模块，提供通用的数据库CRUD操作。
"""
from typing import Dict, List, Optional, Type, TypeVar, Union, Any, Generic

from pydantic import BaseModel
from sqlalchemy import select, update, delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database.connection import get_db_session
from app.models.base import Base

# 定义泛型类型变量
ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """
    提供通用的CRUD操作基类。
    
    Attributes:
        model: SQLAlchemy模型类
    """
    
    def __init__(self, model: Type[ModelType]):
        """
        初始化CRUD操作类。
        
        Args:
            model: SQLAlchemy模型类
        """
        self.model = model
    
    def create(self, db: Session, *, obj_in: Union[CreateSchemaType, Dict[str, Any]]) -> ModelType:
        """
        创建新记录。
        
        Args:
            db: 数据库会话
            obj_in: 创建对象的数据，可以是Pydantic模型或字典
            
        Returns:
            ModelType: 创建的记录
        """
        if isinstance(obj_in, dict):
            obj_in_data = obj_in
        else:
            obj_in_data = obj_in.dict(exclude_unset=True)
        
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """
        根据ID获取记录。
        
        Args:
            db: 数据库会话
            id: 记录ID
            
        Returns:
            Optional[ModelType]: 查询到的记录，如果不存在则返回None
        """
        return db.query(self.model).filter(self.model.id == id).first()
    
    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """
        获取多条记录。
        
        Args:
            db: 数据库会话
            skip: 跳过的记录数
            limit: 返回的最大记录数
            
        Returns:
            List[ModelType]: 记录列表
        """
        return db.query(self.model).offset(skip).limit(limit).all()
    
    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]]
    ) -> ModelType:
        """
        更新记录。
        
        Args:
            db: 数据库会话
            db_obj: 要更新的数据库对象
            obj_in: 更新的数据，可以是Pydantic模型或字典
            
        Returns:
            ModelType: 更新后的记录
        """
        obj_data = db.query(self.model).filter(self.model.id == db_obj.id).first().__dict__
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        
        for field in obj_data:
            if field in update_data:
                setattr(db_obj, field, update_data[field])
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
    
    def remove(self, db: Session, *, id: int) -> ModelType:
        """
        删除记录。
        
        Args:
            db: 数据库会话
            id: 记录ID
            
        Returns:
            ModelType: 被删除的记录
        """
        obj = db.query(self.model).get(id)
        db.delete(obj)
        db.commit()
        return obj


def create_record(model: Type[ModelType], data: Dict[str, Any]) -> ModelType:
    """
    创建记录的辅助函数。
    
    Args:
        model: 模型类
        data: 创建数据
        
    Returns:
        ModelType: 创建的记录
    """
    with get_db_session() as session:
        try:
            db_obj = model(**data)
            session.add(db_obj)
            session.commit()
            session.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            session.rollback()
            raise e


def update_record(model: Type[ModelType], id: int, data: Dict[str, Any]) -> Optional[ModelType]:
    """
    更新记录的辅助函数。
    
    Args:
        model: 模型类
        id: 记录ID
        data: 更新数据
        
    Returns:
        Optional[ModelType]: 更新后的记录，如果记录不存在则返回None
    """
    with get_db_session() as session:
        try:
            stmt = (
                update(model)
                .where(model.id == id)
                .values(**data)
                .returning(model)
            )
            result = session.execute(stmt)
            session.commit()
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            session.rollback()
            raise e


def delete_record(model: Type[ModelType], id: int) -> bool:
    """
    删除记录的辅助函数。
    
    Args:
        model: 模型类
        id: 记录ID
        
    Returns:
        bool: 删除成功返回True，记录不存在返回False
    """
    with get_db_session() as session:
        try:
            stmt = delete(model).where(model.id == id)
            result = session.execute(stmt)
            session.commit()
            return result.rowcount > 0
        except SQLAlchemyError as e:
            session.rollback()
            raise e


def get_record_by_id(model: Type[ModelType], id: int) -> Optional[ModelType]:
    """
    根据ID获取记录的辅助函数。
    
    Args:
        model: 模型类
        id: 记录ID
        
    Returns:
        Optional[ModelType]: 查询到的记录，如果不存在则返回None
    """
    with get_db_session() as session:
        try:
            stmt = select(model).where(model.id == id)
            result = session.execute(stmt)
            return result.scalar_one_or_none()
        except SQLAlchemyError as e:
            raise e


def get_records(
    model: Type[ModelType],
    *,
    skip: int = 0,
    limit: int = 100,
    filters: Optional[Dict[str, Any]] = None
) -> List[ModelType]:
    """
    获取多条记录的辅助函数。
    
    Args:
        model: 模型类
        skip: 跳过的记录数
        limit: 返回的最大记录数
        filters: 过滤条件
        
    Returns:
        List[ModelType]: 记录列表
    """
    with get_db_session() as session:
        try:
            stmt = select(model)
            
            if filters:
                for key, value in filters.items():
                    if hasattr(model, key):
                        stmt = stmt.where(getattr(model, key) == value)
            
            stmt = stmt.offset(skip).limit(limit)
            result = session.execute(stmt)
            return result.scalars().all()
        except SQLAlchemyError as e:
            raise e 