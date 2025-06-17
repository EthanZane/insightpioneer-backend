"""
数据库连接模块，提供数据库连接管理功能。
"""
import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv
from loguru import logger

from app.config.settings import get_settings

# 加载环境变量
load_dotenv()

# 获取数据库连接URL
def get_database_url() -> str:
    """
    获取数据库连接URL，优先从环境变量中获取。
    
    Returns:
        str: 数据库连接URL
    """
    settings = get_settings()
    return os.getenv("DATABASE_URL", settings.DATABASE_URL)

# 创建数据库引擎
def create_db_engine() -> Engine:
    """
    创建SQLAlchemy数据库引擎。
    
    Returns:
        Engine: SQLAlchemy数据库引擎
    """
    database_url = get_database_url()
    logger.info(f"创建数据库引擎，连接到: {database_url.split('@')[-1] if '@' in database_url else database_url}")
    return create_engine(
        database_url,
        pool_pre_ping=True,  # 连接前ping一下，确保连接有效
        pool_recycle=1800,   # 30分钟后回收连接
        echo=False,          # 不打印SQL语句，减少日志输出
        connect_args={
            "connect_timeout": 30,  # 30秒连接超时
            "application_name": "InsightPioneer"  # 标识应用名称
        }
    )

# 创建会话工厂
def create_session_factory():
    """
    创建会话工厂。
    
    Returns:
        sessionmaker: 会话工厂
    """
    engine = create_db_engine()
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 获取数据库会话
SessionLocal = create_session_factory()

@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    获取数据库会话的上下文管理器。
    
    Yields:
        Session: 数据库会话
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def init_db() -> None:
    """
    初始化数据库，创建所有表。
    """
    from app.models.base import Base
    from app.models.site import MonitoredSite, DiscoveredPage, CrawlLog
    
    engine = create_db_engine()
    logger.info("开始创建数据库表...")
    
    # 确保所有模型类都被导入
    tables = [table.__tablename__ for table in [MonitoredSite, DiscoveredPage, CrawlLog]]
    logger.info(f"将要创建的表: {', '.join(tables)}")
    
    # 显式创建所有表
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("所有表创建完成")
    except Exception as e:
        logger.error(f"创建表时出错: {str(e)}")
        raise
    
    # 验证表是否创建成功
    from sqlalchemy import inspect
    inspector = inspect(engine)
    actual_tables = inspector.get_table_names()
    logger.info(f"数据库中的实际表: {', '.join(actual_tables)}")
    
    # 检查我们的表是否都被创建
    missing_tables = [table for table in tables if table not in actual_tables]
    if missing_tables:
        logger.error(f"以下表未被创建: {', '.join(missing_tables)}")
    else:
        logger.info("验证成功: 所有表都已创建") 