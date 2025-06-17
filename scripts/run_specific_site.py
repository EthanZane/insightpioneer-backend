#!/usr/bin/env python
"""
运行特定站点的爬虫脚本。
"""
import os
import sys

# 将项目根目录添加到Python路径
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

import argparse
from typing import Optional

from loguru import logger

from app.config.logging import setup_logging
from app.config.settings import get_settings
from app.database.connection import get_db_session, init_db
from app.models.site import MonitoredSite
from app.scrapers.sitemap.run import run_crawler as run_sitemap_crawler


def parse_args() -> argparse.Namespace:
    """
    解析命令行参数。
    
    Returns:
        argparse.Namespace: 解析后的参数
    """
    parser = argparse.ArgumentParser(description="运行特定站点的爬虫")
    
    parser.add_argument(
        "site_id",
        type=int,
        help="要运行的监控站点ID"
    )
    
    parser.add_argument(
        "--no-title",
        action="store_true",
        help="不获取页面标题"
    )
    
    parser.add_argument(
        "--no-notify",
        action="store_true",
        help="不发送通知"
    )
    
    return parser.parse_args()


def get_site_monitoring_type(site_id: int) -> Optional[str]:
    """
    获取站点的监控类型。
    
    Args:
        site_id: 站点ID
        
    Returns:
        Optional[str]: 站点的监控类型，如果找不到站点则返回None
    """
    with get_db_session() as session:
        site = session.query(MonitoredSite).filter(
            MonitoredSite.id == site_id,
            MonitoredSite.is_enabled == 1
        ).first()
        
        if not site:
            logger.error(f"找不到ID为 {site_id} 的启用站点")
            return None
        
        return site.monitoring_type


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
    
    # 初始化数据库
    init_db()
    
    # 获取站点监控类型
    monitoring_type = get_site_monitoring_type(args.site_id)
    
    if not monitoring_type:
        return 1
    
    # 根据监控类型选择爬虫
    success = False
    if monitoring_type == "sitemap":
        # 运行Sitemap爬虫
        success = run_sitemap_crawler(
            site_id=args.site_id,
            fetch_title=not args.no_title,
            enable_notification=not args.no_notify
        )
    elif monitoring_type == "partial_crawl":
        # TODO: 运行局部爬虫
        logger.error("局部爬虫尚未实现")
        return 1
    elif monitoring_type == "full_crawl":
        # TODO: 运行全站爬虫
        logger.error("全站爬虫尚未实现")
        return 1
    else:
        logger.error(f"未知的监控类型: {monitoring_type}")
        return 1
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main()) 