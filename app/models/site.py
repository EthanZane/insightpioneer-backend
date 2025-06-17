"""
站点模型模块，定义监控站点相关的数据库模型。
"""
from datetime import datetime
from typing import List, Optional

from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import relationship

from app.models.base import Base
from app.utils.time import utc_now


class MonitoredSite(Base):
    """
    监控站点模型，存储用户配置的监控目标。
    
    Attributes:
        name: 站点名称
        base_url: 站点基础URL
        monitoring_type: 监控类型 (sitemap, full_crawl, partial_crawl)
        sitemap_url: Sitemap URL (仅在monitoring_type=sitemap时使用)
        crawl_config_json: 爬取配置JSON
        user_agent: 自定义User-Agent
        proxy_config_json: 代理配置JSON
        fetch_title_for_sitemap_urls: 是否为Sitemap发现的URL获取标题 (0=否, 1=是)
        is_enabled: 是否启用 (0=否, 1=是)
        is_notification_enabled: 是否启用通知 (0=否, 1=是)
        last_crawled_at: 最后爬取时间
        pages: 与该站点关联的已发现页面
        logs: 与该站点关联的爬取日志
    """
    __tablename__ = "insight_monitored_sites"
    
    name = Column(String(255), nullable=False)
    base_url = Column(String(2048), nullable=False)
    monitoring_type = Column(String(50), nullable=False)
    sitemap_url = Column(String(2048))
    crawl_config_json = Column(JSON)
    user_agent = Column(String(255))
    proxy_config_json = Column(JSON)
    fetch_title_for_sitemap_urls = Column(Integer, default=1, server_default='1', nullable=False)
    is_enabled = Column(Integer, default=1, server_default='1', nullable=False)
    is_notification_enabled = Column(Integer, default=1, server_default='1', nullable=False)
    last_crawled_at = Column(DateTime(timezone=True))
    
    # 不使用关系属性，避免循环引用问题
    # 这些关系会在表创建后在查询时使用
    
    def __init__(self, **kwargs):
        """
        初始化监控站点。
        
        Args:
            **kwargs: 关键字参数
        """
        super().__init__(**kwargs)
        
        # 验证监控类型
        valid_types = ["sitemap", "full_crawl", "partial_crawl"]
        if self.monitoring_type not in valid_types:
            raise ValueError(f"监控类型 '{self.monitoring_type}' 无效。有效的类型有: {', '.join(valid_types)}")
        
        # Sitemap监控类型需要sitemap_url
        if self.monitoring_type == "sitemap" and not self.sitemap_url:
            raise ValueError("监控类型为'sitemap'时，必须提供'sitemap_url'。")


class DiscoveredPage(Base):
    """
    已发现页面模型，存储爬虫发现的页面。
    
    Attributes:
        monitored_site_id: 关联的监控站点ID
        url: 页面URL
        page_title: 页面标题
        first_discovered_at: 首次发现时间
        last_seen_at: 最后一次看到的时间
        is_processed: 是否已处理 (0=否, 1=是)
        site: 关联的监控站点
    """
    __tablename__ = "insight_discovered_pages"
    
    monitored_site_id = Column(Integer, ForeignKey("insight_monitored_sites.id", ondelete="CASCADE"), nullable=False)
    url = Column(Text, nullable=False)
    page_title = Column(Text)
    first_discovered_at = Column(DateTime(timezone=True), default=utc_now, server_default=func.now(), nullable=False)
    last_seen_at = Column(DateTime(timezone=True), default=utc_now, server_default=func.now(), nullable=False)
    is_processed = Column(Integer, default=0, server_default='0', nullable=False)
    
    # 不使用关系属性，避免循环引用问题
    
    # 唯一约束 (一个站点下不能有重复的URL)
    __table_args__ = (
        UniqueConstraint("monitored_site_id", "url", name="uix_site_url"),
    )


class CrawlLog(Base):
    """
    爬取日志模型，记录爬取过程。
    
    Attributes:
        monitored_site_id: 关联的监控站点ID
        run_id: GitHub Actions运行ID
        start_time: 开始时间
        end_time: 结束时间
        status: 状态 (success, partial_success, failed)
        pages_found_count: 发现的页面数
        message: 日志消息
        site: 关联的监控站点
    """
    __tablename__ = "insight_crawl_logs"
    
    monitored_site_id = Column(Integer, ForeignKey("insight_monitored_sites.id", ondelete="CASCADE"), nullable=False)
    run_id = Column(String(255))
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True))
    status = Column(String(50), nullable=False)
    pages_found_count = Column(Integer, default=0, server_default='0')
    message = Column(Text)
    
    # 不使用关系属性，避免循环引用问题
    
    def __init__(self, **kwargs):
        """
        初始化爬取日志。
        
        Args:
            **kwargs: 关键字参数
        """
        super().__init__(**kwargs)
        
        # 验证状态
        valid_statuses = ["success", "partial_success", "failed"]
        if self.status not in valid_statuses:
            raise ValueError(f"状态 '{self.status}' 无效。有效的状态有: {', '.join(valid_statuses)}")


# 在所有表定义完成后，添加关系
MonitoredSite.pages = relationship("DiscoveredPage", backref="site", cascade="all, delete-orphan")
MonitoredSite.logs = relationship("CrawlLog", backref="site", cascade="all, delete-orphan") 