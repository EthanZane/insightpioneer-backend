#!/usr/bin/env python
"""
数据库初始化脚本，用于创建表结构。
"""
import os
import sys

# 将项目根目录添加到Python路径
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

import argparse
import time

from loguru import logger
from sqlalchemy import text

from app.config.logging import setup_logging
from app.database.connection import init_db, get_database_url, create_db_engine


def parse_args() -> argparse.Namespace:
    """
    解析命令行参数。
    
    Returns:
        argparse.Namespace: 解析后的参数
    """
    parser = argparse.ArgumentParser(description="数据库初始化脚本")
    
    parser.add_argument(
        "--force",
        action="store_true",
        help="强制重新创建表（危险操作，会删除所有数据）"
    )
    
    return parser.parse_args()


def force_recreate_tables() -> bool:
    """
    强制重新创建所有表（先删除后创建）。
    
    Returns:
        bool: 操作是否成功
    """
    from app.models.base import Base
    from app.models.site import MonitoredSite, DiscoveredPage, CrawlLog
    
    engine = create_db_engine()
    
    try:
        # 先删除所有表
        logger.warning("开始删除所有现有表...")
        Base.metadata.drop_all(bind=engine)
        logger.info("所有表已删除")
        
        # 等待一秒，确保删除操作完成
        time.sleep(1)
        
        # 重新创建所有表
        logger.info("开始重新创建所有表...")
        Base.metadata.create_all(bind=engine)
        logger.info("所有表重新创建完成")
        
        # 验证表是否创建成功
        from sqlalchemy import inspect
        inspector = inspect(engine)
        actual_tables = inspector.get_table_names()
        
        tables = [table.__tablename__ for table in [MonitoredSite, DiscoveredPage, CrawlLog]]
        missing_tables = [table for table in tables if table not in actual_tables]
        
        if missing_tables:
            logger.error(f"以下表未被创建: {', '.join(missing_tables)}")
            return False
        else:
            logger.info("验证成功: 所有表都已重新创建")
            return True
            
    except Exception as e:
        logger.exception(f"重新创建表时出错: {str(e)}")
        return False


def main() -> int:
    """
    主函数。
    
    Returns:
        int: 退出码，0表示成功，非0表示失败
    """
    # 设置日志
    setup_logging()
    
    # 解析命令行参数
    args = parse_args()
    
    try:
        # 打印数据库连接信息（隐藏密码）
        db_url = get_database_url()
        masked_url = db_url
        if "://" in db_url:
            parts = db_url.split("://", 1)
            if "@" in parts[1]:
                auth, rest = parts[1].split("@", 1)
                masked_url = f"{parts[0]}://****:****@{rest}"
        
        logger.info(f"正在连接数据库: {masked_url}")
        
        if args.force:
            logger.warning("即将重新创建所有表，这将删除所有数据！")
            logger.warning("您有 5 秒钟时间按 Ctrl+C 取消操作...")
            
            # 倒计时
            for i in range(5, 0, -1):
                logger.warning(f"删除倒计时: {i} 秒...")
                time.sleep(1)
            
            # 执行强制重新创建表
            success = force_recreate_tables()
            return 0 if success else 1
        else:
            # 初始化数据库（创建表）
            logger.info("正在初始化数据库...")
            init_db()
            
            # 这里不再尝试使用ORM验证表，因为可能会触发关系加载问题
            # 我们已经在init_db函数中添加了验证代码
            
            return 0
            
    except Exception as e:
        logger.exception(f"数据库初始化失败: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 