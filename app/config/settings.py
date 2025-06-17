"""
全局配置设置模块，提供项目所需的配置项。
"""
import os
from functools import lru_cache
from typing import Any, Dict, Optional, List

from pydantic import PostgresDsn, validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """
    应用配置设置类。
    
    Attributes:
        PROJECT_NAME: 项目名称
        DESCRIPTION: 项目描述
        VERSION: 项目版本
        DATABASE_URL: 数据库连接URL
        FEISHU_WEBHOOK_URL: 飞书机器人Webhook URL
        FEISHU_SECRET: 飞书机器人签名密钥
        DEFAULT_USER_AGENT: 默认User-Agent
        DEFAULT_CRAWL_FREQUENCY_MINUTES: 默认爬取频率（分钟）
        DEFAULT_CRAWL_DEPTH: 默认爬取深度
        DEFAULT_CRAWL_CONCURRENCY: 默认爬取并发数
        DEFAULT_CRAWL_DELAY: 默认爬取延迟（秒）
        DEFAULT_RESPECT_ROBOTS_TXT: 默认是否遵循robots.txt
        DEFAULT_FETCH_TITLE_FOR_SITEMAP_URLS: 默认是否为Sitemap发现的URL获取标题
    """
    PROJECT_NAME: str = "InsightPioneer"
    DESCRIPTION: str = "Website Monitoring System"
    VERSION: str = "0.1.0"
    
    # 数据库设置
    DATABASE_URL: PostgresDsn = "postgresql://postgres:postgres@localhost:5432/insightpioneer"
    
    # 通知设置
    FEISHU_WEBHOOK_URL: Optional[str] = None
    FEISHU_SECRET: Optional[str] = None
    
    # 爬虫设置
    DEFAULT_USER_AGENT: str = "InsightPioneer/0.1.0 (+https://github.com/username/insightpioneer-backend)"
    DEFAULT_CRAWL_FREQUENCY_MINUTES: int = 1440  # 24小时
    DEFAULT_CRAWL_DEPTH: int = 3
    DEFAULT_CRAWL_CONCURRENCY: int = 2
    DEFAULT_CRAWL_DELAY: float = 1.0
    DEFAULT_RESPECT_ROBOTS_TXT: bool = True
    DEFAULT_FETCH_TITLE_FOR_SITEMAP_URLS: bool = True
    
    # User Agent列表（用于轮换）
    USER_AGENT_LIST: List[str] = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (iPad; CPU OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59",
    ]
    
    # HTTP请求设置
    HTTP_TIMEOUT: int = 30
    HTTP_MAX_RETRIES: int = 3
    HTTP_RETRY_DELAY: int = 5
    
    # 数据库连接池设置
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    
    # 日志设置
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """
    获取应用配置实例，使用lru_cache缓存结果。
    
    Returns:
        Settings: 配置实例
    """
    return Settings()


def get_environment() -> str:
    """
    获取当前运行环境。
    
    Returns:
        str: 环境名称（development, testing, production）
    """
    return os.getenv("ENVIRONMENT", "development") 