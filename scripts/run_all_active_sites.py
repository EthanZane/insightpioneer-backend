#!/usr/bin/env python
"""
运行所有活跃站点的爬虫脚本。
"""
import os
import sys

# 将项目根目录添加到Python路径
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

import time
from datetime import datetime, timedelta
from typing import List, Tuple

from loguru import logger

from app.config.logging import setup_logging
from app.config.settings import get_settings
from app.database.connection import get_db_session, init_db
from app.models.site import MonitoredSite
from app.scrapers.sitemap.crawler import SitemapCrawler


def get_sites_to_run() -> List[Tuple[int, str, str]]:
    """
    获取需要运行的站点列表。
    
    Returns:
        List[Tuple[int, str, str]]: (站点ID, 站点名称, 监控类型) 列表
    """
    sites_to_run = []
    
    with get_db_session() as session:
        # 查询所有启用的站点
        sites = session.query(MonitoredSite).filter(
            MonitoredSite.is_enabled == 1
        ).all()
        
        for site in sites:
            # 所有启用的站点都需要运行
            sites_to_run.append((site.id, site.name, site.monitoring_type))
    
    return sites_to_run


def main() -> int:
    """
    主函数。
    
    Returns:
        int: 退出码，0表示成功，非0表示失败
    """
    # 设置日志
    setup_logging()
    
    # 初始化数据库
    init_db()
    
    print("\n" + "="*50)
    print(">>> 站点监控任务开始执行")
    print("="*50)
    
    # 获取需要运行的站点
    sites_to_run = get_sites_to_run()
    
    if not sites_to_run:
        print(">>> 没有需要运行的站点")
        return 0
    
    print(f">>> 共找到 {len(sites_to_run)} 个需要监控的站点")
    print("-"*50)
    
    # 运行每个站点
    success_count = 0
    start_time = time.time()
    
    for idx, (site_id, site_name, monitoring_type) in enumerate(sites_to_run, 1):
        site_start_time = time.time()
        print(f"\n>>> [{idx}/{len(sites_to_run)}] 开始采集站点: {site_name} (ID: {site_id}, 类型: {monitoring_type})")
        
        try:
            # 确保在每个站点的处理中使用单独的会话
            with get_db_session() as session:
                # 从会话中获取最新的站点对象
                site = session.query(MonitoredSite).filter(
                    MonitoredSite.id == site_id,
                    MonitoredSite.is_enabled == 1
                ).first()
                
                if not site:
                    print(f">>> 站点 {site_name} (ID: {site_id}) 不存在或已被禁用，跳过")
                    continue
                
                if monitoring_type == "sitemap":
                    print(f">>> 开始使用Sitemap方式采集: {site_name} - {site.sitemap_url}")
                    
                    # 运行Sitemap爬虫，传递会话和站点对象
                    # 创建爬虫实例
                    crawler = SitemapCrawler(
                        site_id=site_id,
                        fetch_title=False,  # 不获取标题
                        notifier=None      # 默认不使用通知器
                    )
                    
                    # 直接调用crawler的process_site方法，传递会话和站点对象
                    try:
                        success, message, new_pages_count = crawler.process_site(session=session, site=site)
                        site_elapsed = time.time() - site_start_time
                        if success:
                            print(f">>> 站点 {site_name} 采集完成: 发现 {new_pages_count} 个新页面，耗时 {site_elapsed:.2f}秒")
                            success_count += 1
                        else:
                            print(f">>> 站点 {site_name} 采集失败: {message}")
                    except Exception as e:
                        print(f">>> 站点 {site_name} 采集过程中出错: {str(e)}")
                        success = False
                elif monitoring_type == "partial_crawl":
                    # TODO: 运行局部爬虫
                    print(f">>> 局部爬虫尚未实现，跳过站点 {site_name}")
                    continue
                elif monitoring_type == "full_crawl":
                    # TODO: 运行全站爬虫
                    print(f">>> 全站爬虫尚未实现，跳过站点 {site_name}")
                    continue
                else:
                    print(f">>> 未知的监控类型: {monitoring_type}，跳过站点 {site_name}")
                    continue
                
                # 添加延迟，避免过快请求
                time.sleep(1)
            
        except Exception as e:
            print(f">>> 处理站点 {site_name} 时出错: {str(e)}")
        
        print(f">>> 站点 {site_name} 处理结束")
        print("-"*50)
    
    total_elapsed = time.time() - start_time
    print("\n" + "="*50)
    print(f">>> 所有站点处理完成: {success_count}/{len(sites_to_run)} 个站点成功")
    print(f">>> 总耗时: {total_elapsed:.2f}秒")
    print("="*50 + "\n")
    
    # 只有所有站点都成功才返回0
    return 0 if success_count == len(sites_to_run) else 1


if __name__ == "__main__":
    sys.exit(main()) 