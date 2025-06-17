#!/usr/bin/env python
"""
创建测试站点数据脚本。
"""
import os
import sys

# 将项目根目录添加到Python路径
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

from loguru import logger
from sqlalchemy import text

from app.config.logging import setup_logging
from app.database.connection import get_db_session, create_db_engine
from app.models.site import MonitoredSite

def main() -> int:
    """
    主函数。
    
    Returns:
        int: 退出码，0表示成功，非0表示失败
    """
    # 设置日志
    setup_logging()
    
    try:
        # 创建测试站点
        logger.info("正在创建测试站点...")
        
        # 先检查表是否存在
        engine = create_db_engine()
        
        # 使用原生SQL检查表是否存在
        with engine.connect() as conn:
            result = conn.execute(text("SELECT to_regclass('insight_monitored_sites')"))
            table_exists = result.scalar()
            
            if not table_exists:
                logger.error("表 'insight_monitored_sites' 不存在，请先运行 init_database.py")
                return 1
            
            logger.info("表 'insight_monitored_sites' 存在，继续创建测试站点")
        
        with get_db_session() as session:
            # 检查是否已存在
            existing = session.query(MonitoredSite).filter(
                MonitoredSite.name == "测试站点"
            ).first()
            
            if existing:
                logger.info(f"测试站点已存在 (ID: {existing.id})")
                return 0
            
            # 创建新站点
            site = MonitoredSite(
                name="测试站点",
                base_url="https://example.com",
                monitoring_type="sitemap",
                sitemap_url="https://example.com/sitemap.xml",
                fetch_title_for_sitemap_urls=1,
                is_enabled=1,
                is_notification_enabled=1
            )
            
            session.add(site)
            try:
                session.commit()
                logger.info(f"测试站点创建成功 (ID: {site.id})")
            except Exception as e:
                session.rollback()
                logger.error(f"提交时出错: {str(e)}")
                raise
        
        return 0
        
    except Exception as e:
        logger.exception(f"创建测试站点失败: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 