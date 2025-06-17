"""
测试配置文件，提供测试所需的fixtures。
"""
import os
import pytest
from datetime import datetime
from typing import Dict, Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.models.base import Base
from app.models.site import MonitoredSite, DiscoveredPage, CrawlLog


@pytest.fixture(scope="session")
def test_engine():
    """
    创建测试数据库引擎。
    
    Returns:
        Engine: SQLAlchemy数据库引擎
    """
    # 使用内存SQLite数据库进行测试
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture(scope="function")
def db_session(test_engine) -> Generator[Session, None, None]:
    """
    创建测试数据库会话。
    
    Args:
        test_engine: 测试数据库引擎
        
    Yields:
        Session: SQLAlchemy会话
    """
    connection = test_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)
    
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def sample_site_data() -> Dict:
    """
    提供示例站点数据。
    
    Returns:
        Dict: 示例站点数据
    """
    return {
        "name": "测试站点",
        "base_url": "https://example.com",
        "monitoring_type": "sitemap",
        "sitemap_url": "https://example.com/sitemap.xml",
        "crawl_config_json": None,
        "monitoring_frequency_minutes": 1440,
        "user_agent": None,
        "proxy_config_json": None,
        "fetch_title_for_sitemap_urls": 1,
        "is_enabled": 1,
        "is_notification_enabled": 1,
    }


@pytest.fixture
def sample_site(db_session, sample_site_data) -> MonitoredSite:
    """
    创建示例站点。
    
    Args:
        db_session: 数据库会话
        sample_site_data: 示例站点数据
        
    Returns:
        MonitoredSite: 创建的站点
    """
    site = MonitoredSite(**sample_site_data)
    db_session.add(site)
    db_session.commit()
    db_session.refresh(site)
    return site


@pytest.fixture
def sample_pages(db_session, sample_site) -> Generator[list, None, None]:
    """
    创建示例页面。
    
    Args:
        db_session: 数据库会话
        sample_site: 示例站点
        
    Yields:
        list: 创建的页面列表
    """
    pages = []
    for i in range(5):
        page = DiscoveredPage(
            monitored_site_id=sample_site.id,
            url=f"https://example.com/page{i}.html",
            page_title=f"测试页面 {i}",
            first_discovered_at=datetime.utcnow(),
            last_seen_at=datetime.utcnow(),
            is_processed=0
        )
        db_session.add(page)
        pages.append(page)
    
    db_session.commit()
    
    for page in pages:
        db_session.refresh(page)
    
    yield pages
    
    # 清理
    for page in pages:
        db_session.delete(page)
    db_session.commit()


@pytest.fixture
def mock_http_response(monkeypatch) -> None:
    """
    模拟HTTP响应。
    
    Args:
        monkeypatch: pytest monkeypatch对象
    """
    class MockResponse:
        def __init__(self, content, status_code=200, headers=None, url=None):
            self.content = content
            self.text = content.decode('utf-8') if isinstance(content, bytes) else content
            self.status_code = status_code
            self.headers = headers or {}
            self.url = url
        
        def raise_for_status(self):
            if self.status_code >= 400:
                from requests.exceptions import HTTPError
                raise HTTPError(f"HTTP Error: {self.status_code}")
    
    def mock_make_request(*args, **kwargs):
        url = kwargs.get('url') or args[0]
        if 'sitemap.xml' in url:
            content = b"""<?xml version="1.0" encoding="UTF-8"?>
            <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
                <url>
                    <loc>https://example.com/page1.html</loc>
                    <lastmod>2023-01-01</lastmod>
                </url>
                <url>
                    <loc>https://example.com/page2.html</loc>
                    <lastmod>2023-01-02</lastmod>
                </url>
            </urlset>"""
        elif 'page1.html' in url or 'page2.html' in url:
            content = f"<html><head><title>Test Page - {url}</title></head><body>Test content</body></html>"
        else:
            content = "<html><body>Default content</body></html>"
        
        return MockResponse(content, 200, {'Content-Type': 'text/html'}, url)
    
    from app.utils import http
    monkeypatch.setattr(http, "make_request", mock_make_request) 