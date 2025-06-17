"""
Sitemap爬虫模块，用于通过Sitemap监控网站变化。
"""
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple

from loguru import logger
from sqlalchemy.orm import Session

from app.config.settings import get_settings
from app.database.connection import get_db_session
from app.models.site import MonitoredSite, DiscoveredPage, CrawlLog
from app.notifiers.feishu import FeishuNotifier
from app.scrapers.sitemap.parser import SitemapParser
from app.utils.http import make_request
from app.utils.time import utc_now, parse_iso_datetime


class SitemapCrawler:
    """
    Sitemap爬虫，用于通过Sitemap监控网站变化。
    """
    
    def __init__(
        self,
        site_id: int,
        fetch_title: bool = False,  # 默认不获取标题
        notifier: Optional[FeishuNotifier] = None
    ):
        """
        初始化Sitemap爬虫。
        
        Args:
            site_id: 监控站点ID
            fetch_title: 是否获取页面标题（已废弃，总是为False）
            notifier: 通知器实例
        """
        self.site_id = site_id
        self.fetch_title = False  # 强制设置为False，不获取页面标题
        self.notifier = notifier or FeishuNotifier()
        self.settings = get_settings()
    
    def load_site_config(self) -> Optional[MonitoredSite]:
        """
        加载站点配置。
        
        Returns:
            Optional[MonitoredSite]: 站点配置，如果加载失败则返回None
        """
        with get_db_session() as session:
            site = session.query(MonitoredSite).filter(
                MonitoredSite.id == self.site_id,
                MonitoredSite.is_enabled == 1
            ).first()
            
            if not site:
                print(f">>> 找不到ID为 {self.site_id} 的启用站点")
                return None
            
            # 验证监控类型
            if site.monitoring_type != "sitemap":
                print(f">>> 站点 {site.name} (ID: {site.id}) 的监控类型不是'sitemap'，而是 '{site.monitoring_type}'")
                return None
            
            # 验证sitemap_url
            if not site.sitemap_url:
                print(f">>> 站点 {site.name} (ID: {site.id}) 未配置Sitemap URL")
                return None
            
            # 确保我们返回会话中的对象，而不是分离的对象
            # 提前获取所有需要的属性，避免对象分离后的懒加载问题
            site_data = {
                "id": site.id,
                "name": site.name,
                "base_url": site.base_url,
                "monitoring_type": site.monitoring_type,
                "sitemap_url": site.sitemap_url,
                "user_agent": site.user_agent,
                "proxy_config_json": site.proxy_config_json,
                "fetch_title_for_sitemap_urls": site.fetch_title_for_sitemap_urls,
                "is_enabled": site.is_enabled,
                "is_notification_enabled": site.is_notification_enabled,
                "last_crawled_at": site.last_crawled_at
            }
            
            # 保存站点数据，以便在process_site中使用
            self.site_data = site_data
            
            return site
    
    def get_existing_urls(self, session: Session, site_id: int) -> Dict[str, datetime]:
        """
        获取已存在的URL及其最后修改时间。
        
        Args:
            session: 数据库会话
            site_id: 站点ID
            
        Returns:
            Dict[str, datetime]: URL到最后修改时间的映射
        """
        from datetime import timezone
        
        existing_pages = session.query(DiscoveredPage).filter(
            DiscoveredPage.monitored_site_id == site_id
        ).all()
        
        url_count = len(existing_pages)
        print(f">>> 数据库中已有 {url_count} 个URL记录")
        
        result = {}
        for page in existing_pages:
            last_seen_at = page.last_seen_at
            # 确保datetime对象有时区信息
            if last_seen_at.tzinfo is None:
                last_seen_at = last_seen_at.replace(tzinfo=timezone.utc)
            result[page.url] = last_seen_at
        
        return result
    
    def fetch_page_title(self, url: str, user_agent: Optional[str] = None, proxy: Optional[str] = None) -> Optional[str]:
        """
        获取页面标题（已废弃，直接返回None）。
        
        Args:
            url: 页面URL
            user_agent: 用户代理字符串
            proxy: 代理服务器URL
            
        Returns:
            Optional[str]: 页面标题，总是返回None
        """
        # 不再获取页面标题
        return None
    
    def create_crawl_log(
        self,
        session: Session,
        site: MonitoredSite,
        status: str,
        pages_found_count: int = 0,
        message: Optional[str] = None
    ) -> CrawlLog:
        """
        创建爬取日志。
        
        Args:
            session: 数据库会话
            site: 监控站点
            status: 状态
            pages_found_count: 发现的页面数
            message: 日志消息
            
        Returns:
            CrawlLog: 创建的爬取日志
        """
        import os
        
        # 获取GitHub运行ID（如果在GitHub Actions中运行）
        run_id = os.environ.get("GITHUB_RUN_ID")
        
        log = CrawlLog(
            monitored_site_id=site.id,
            run_id=run_id,
            start_time=self.start_time,
            end_time=utc_now(),
            status=status,
            pages_found_count=pages_found_count,
            message=message
        )
        
        session.add(log)
        session.commit()
        
        return log
    
    def update_site_last_crawled(self, session: Session, site: MonitoredSite) -> None:
        """
        更新站点最后爬取时间。
        
        Args:
            session: 数据库会话
            site: 监控站点
        """
        site.last_crawled_at = utc_now()
        session.add(site)
        session.commit()
    
    def process_site(self, session=None, site=None) -> Tuple[bool, str, int]:
        """
        处理站点，执行Sitemap监控（只解析sitemap XML，不访问页面内容）。
        
        Args:
            session: 数据库会话对象
            site: 站点对象
            
        Returns:
            Tuple[bool, str, int]: (是否成功, 状态消息, 发现的新页面数)
        """
        self.start_time = utc_now()
        
        # 如果没有传入session和site，则加载站点配置
        if session is None or site is None:
            site = self.load_site_config()
            if not site:
                return False, "站点配置加载失败", 0
        
        # 从配置解析附加设置
        user_agent = site.user_agent or self.settings.DEFAULT_USER_AGENT
        proxy = None
        if site.proxy_config_json:
            try:
                proxy_config = json.loads(site.proxy_config_json)
                proxy = proxy_config.get("proxy_url")
            except (json.JSONDecodeError, TypeError):
                print(f">>> 站点 {site.name} 的代理配置解析失败")
        
        # 确定是否获取标题 - 始终为False
        fetch_title = False
        
        # 创建Sitemap解析器
        parser = SitemapParser(
            user_agent=user_agent,
            proxy=proxy,
            timeout=self.settings.HTTP_TIMEOUT
        )
        
        try:
            # 使用传入的session，或者创建新的session
            if session is None:
                _session = get_db_session()
                context_session = _session.__enter__()
                new_session = True
            else:
                context_session = session
                new_session = False
            
            try:
                # 获取已存在的URL
                existing_urls = self.get_existing_urls(context_session, site.id)
                
                # 解析Sitemap
                print(f">>> 开始从 {site.sitemap_url} 解析Sitemap")
                start_time = time.time()
                sitemap_entries = parser.extract_urls_from_sitemap(site.sitemap_url, site.base_url)
                elapsed = time.time() - start_time
                print(f">>> Sitemap解析完成，共找到 {len(sitemap_entries)} 个URL，耗时 {elapsed:.2f}秒")
                
                # 找出新URL
                new_pages = []
                
                print(">>> 开始处理URL记录...")
                proc_start_time = time.time()
                
                for i, entry in enumerate(sitemap_entries):
                    # 每处理1000个URL打印一次进度
                    if i > 0 and i % 1000 == 0:
                        print(f">>> 已处理 {i}/{len(sitemap_entries)} 个URL...")
                    
                    url = entry["url"]
                    lastmod_str = entry.get("lastmod")
                    lastmod = parse_iso_datetime(lastmod_str) if lastmod_str else None
                    
                    if url in existing_urls:
                        # URL已存在，更新last_seen_at为当前时间（表示这次爬取看到了它）
                        page = context_session.query(DiscoveredPage).filter(
                            DiscoveredPage.monitored_site_id == site.id,
                            DiscoveredPage.url == url
                        ).first()
                        
                        if page:
                            page.last_seen_at = utc_now()
                            context_session.add(page)
                            # 这不算"更新"的页面，只是重新看到了已存在的页面
                    else:
                        # 新URL
                        # 不再获取页面标题
                        title = None
                        
                        # 创建新页面记录
                        page = DiscoveredPage(
                            monitored_site_id=site.id,
                            url=url,
                            page_title=title,
                            first_discovered_at=utc_now(),
                            last_seen_at=utc_now(),
                            is_processed=0
                        )
                        
                        context_session.add(page)
                        new_pages.append(page)
                
                proc_elapsed = time.time() - proc_start_time
                print(f">>> URL处理完成，耗时 {proc_elapsed:.2f}秒")
                
                # 提交更改
                if new_pages:
                    print(f">>> 保存数据: {len(new_pages)} 个新页面")
                    save_start = time.time()
                    context_session.commit()
                    save_elapsed = time.time() - save_start
                    print(f">>> 数据保存完成，耗时 {save_elapsed:.2f}秒")
                else:
                    print(">>> 没有新页面，但仍需保存existing URL的last_seen_at更新")
                    context_session.commit()
                
                # 更新站点最后爬取时间
                self.update_site_last_crawled(context_session, site)
                
                # 创建爬取日志
                self.create_crawl_log(
                    context_session,
                    site,
                    status="success",
                    pages_found_count=len(new_pages),
                    message=f"发现 {len(new_pages)} 个新页面"
                )
                
                # 发送通知
                if new_pages and site.is_notification_enabled:
                    self.notifier.send_new_pages_notification(site, new_pages)
                
                return True, f"成功，发现 {len(new_pages)} 个新页面", len(new_pages)
            finally:
                # 如果新建了session，则关闭它
                if new_session:
                    _session.__exit__(None, None, None)
                
        except Exception as e:
            print(f">>> 处理站点 {site.name} (ID: {site.id}) 时出错: {str(e)}")
            
            with get_db_session() as error_session:
                # 获取站点对象
                if site is None:
                    site = error_session.query(MonitoredSite).filter(
                        MonitoredSite.id == self.site_id
                    ).first()
                
                if site:
                    # 创建爬取日志
                    self.create_crawl_log(
                        error_session,
                        site,
                        status="failed",
                        message=f"处理失败: {str(e)}"
                    )
                    
                    # 发送错误通知
                    if site.is_notification_enabled:
                        self.notifier.send_error_notification(site, str(e))
                
                return False, f"失败: {str(e)}", 0