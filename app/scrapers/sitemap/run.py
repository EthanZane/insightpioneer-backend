"""
Sitemap爬虫运行模块，提供命令行接口来运行Sitemap爬虫。
"""
import argparse
import sys
from typing import List, Optional

from loguru import logger

from app.config.logging import setup_logging
from app.config.settings import get_settings
from app.database.connection import init_db, get_db_session
from app.notifiers.feishu import FeishuNotifier
from app.scrapers.sitemap.crawler import SitemapCrawler


def parse_args() -> argparse.Namespace:
    """
    解析命令行参数。
    
    Returns:
        argparse.Namespace: 解析后的参数
    """
    parser = argparse.ArgumentParser(description="Sitemap爬虫运行脚本")
    
    parser.add_argument(
        "--config-id",
        type=int,
        required=True,
        help="监控站点ID"
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


def run_crawler(
    site_id: int,
    fetch_title: bool = True,
    enable_notification: bool = True
) -> bool:
    """
    运行Sitemap爬虫。
    
    Args:
        site_id: 监控站点ID
        fetch_title: 是否获取页面标题
        enable_notification: 是否启用通知
        
    Returns:
        bool: 爬取是否成功
    """
    # 初始化通知器
    notifier = None
    if enable_notification:
        notifier = FeishuNotifier()
    
    # 创建爬虫
    crawler = SitemapCrawler(
        site_id=site_id,
        fetch_title=fetch_title,
        notifier=notifier
    )
    
    try:
        # 在同一个会话中执行爬虫操作，避免对象分离
        with get_db_session() as session:
            # 预先加载站点对象
            from app.models.site import MonitoredSite
            site = session.query(MonitoredSite).filter(
                MonitoredSite.id == site_id,
                MonitoredSite.is_enabled == 1
            ).first()
            
            if not site:
                logger.error(f"找不到ID为 {site_id} 的启用站点")
                return False
                
            # 运行爬虫，直接传递session和site对象
            success, message, new_pages_count = crawler.process_site(session=session, site=site)
            
            # 打印结果
            if success:
                logger.info(f"站点 {site_id} 爬取成功: {message}")
            else:
                logger.error(f"站点 {site_id} 爬取失败: {message}")
            
            return success
    except Exception as e:
        logger.exception(f"站点 {site_id} 爬取过程中出错: {str(e)}")
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
    
    # 初始化数据库
    init_db()
    
    # 运行爬虫
    success = run_crawler(
        site_id=args.config_id,
        fetch_title=not args.no_title,
        enable_notification=not args.no_notify
    )
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main()) 