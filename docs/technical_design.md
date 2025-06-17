# 洞察先锋 (InsightPioneer) 技术设计文档

## 1. 系统架构

### 1.1 概述

洞察先锋采用分布式架构，主要包含以下组件：

1. **爬虫模块**：Python脚本，负责爬取监控网站并发现新页面
2. **数据库**：PostgreSQL，存储监控配置和发现的页面
3. **调度系统**：GitHub Actions，定时触发爬虫任务
4. **通知服务**：飞书机器人，发送新页面通知
5. **前端应用**：Next.js应用，提供用户界面（独立仓库）

### 1.2 系统流程

```
[GitHub Actions] --> 触发 --> [爬虫模块] --> 爬取 --> [目标网站]
                                  |
                                  v
[飞书通知] <-- 发送通知 <-- [数据库] <-- 存储数据 <-- [爬虫模块]
    ^                        ^
    |                        |
    +-------- 读取 <---------+------- 读取/写入 <---- [前端应用]
```

## 2. 数据模型

### 2.1 数据库Schema

#### 2.1.1 `monitored_sites` 表

监控站点配置表，存储用户配置的监控目标。

```sql
CREATE TABLE monitored_sites (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    base_url VARCHAR(2048) NOT NULL,
    monitoring_type VARCHAR(50) NOT NULL CHECK (monitoring_type IN ('sitemap', 'full_crawl', 'partial_crawl')),
    sitemap_url VARCHAR(2048),
    crawl_config_json JSONB,
    monitoring_frequency_minutes INTEGER NOT NULL DEFAULT 1440,
    user_agent VARCHAR(255),
    proxy_config_json JSONB,
    fetch_title_for_sitemap_urls SMALLINT NOT NULL DEFAULT 1,
    is_enabled SMALLINT NOT NULL DEFAULT 1,
    is_notification_enabled SMALLINT NOT NULL DEFAULT 1,
    last_crawled_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

其中`crawl_config_json`存储不同监控类型的特定配置：

- 全站爬取示例：
```json
{
    "depth_limit": 3,
    "respect_robots_txt": 1,
    "include_patterns": ["/products/"],
    "exclude_patterns": ["/archive/"]
}
```

- 局部爬取示例：
```json
{
    "entry_page_url": "https://example.com/news",
    "link_selector": "article.news-item a.title-link",
    "title_selector_override": "article.news-item a.title-link h3"
}
```

#### 2.1.2 `discovered_pages` 表

存储已发现的页面信息。

```sql
CREATE TABLE discovered_pages (
    id SERIAL PRIMARY KEY,
    monitored_site_id INTEGER NOT NULL REFERENCES monitored_sites(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    page_title TEXT,
    first_discovered_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_processed SMALLINT NOT NULL DEFAULT 0,
    UNIQUE (monitored_site_id, url)
);
```

#### 2.1.3 `crawl_logs` 表

存储爬取日志，用于追踪和排错。

```sql
CREATE TABLE crawl_logs (
    id SERIAL PRIMARY KEY,
    monitored_site_id INTEGER NOT NULL REFERENCES monitored_sites(id) ON DELETE CASCADE,
    run_id VARCHAR(255),
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) NOT NULL CHECK (status IN ('success', 'partial_success', 'failed')),
    pages_found_count INTEGER DEFAULT 0,
    message TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

### 2.2 数据模型类

使用Python的SQLAlchemy ORM映射数据库表：

```python
# app/models/site.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class MonitoredSite(Base):
    __tablename__ = 'monitored_sites'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    base_url = Column(String(2048), nullable=False)
    monitoring_type = Column(String(50), nullable=False)
    sitemap_url = Column(String(2048))
    crawl_config_json = Column(JSON)
    monitoring_frequency_minutes = Column(Integer, default=1440, nullable=False)
    user_agent = Column(String(255))
    proxy_config_json = Column(JSON)
    fetch_title_for_sitemap_urls = Column(Integer, default=1, nullable=False)
    is_enabled = Column(Integer, default=1, nullable=False)
    is_notification_enabled = Column(Integer, default=1, nullable=False)
    last_crawled_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)

class DiscoveredPage(Base):
    __tablename__ = 'discovered_pages'
    
    id = Column(Integer, primary_key=True)
    monitored_site_id = Column(Integer, ForeignKey('monitored_sites.id', ondelete='CASCADE'), nullable=False)
    url = Column(Text, nullable=False)
    page_title = Column(Text)
    first_discovered_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    last_seen_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    is_processed = Column(Integer, default=0, nullable=False)
    
    __table_args__ = (
        UniqueConstraint('monitored_site_id', 'url'),
    )

class CrawlLog(Base):
    __tablename__ = 'crawl_logs'
    
    id = Column(Integer, primary_key=True)
    monitored_site_id = Column(Integer, ForeignKey('monitored_sites.id', ondelete='CASCADE'), nullable=False)
    run_id = Column(String(255))
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True))
    status = Column(String(50), nullable=False)
    pages_found_count = Column(Integer, default=0)
    message = Column(Text)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
```

## 3. 模块设计

### 3.1 爬虫模块

爬虫模块是核心功能模块，分为三个主要部分：

#### 3.1.1 Sitemap爬虫

```
app/scrapers/sitemap/
├── run.py         # 主入口，处理命令行参数
├── crawler.py     # 核心爬取逻辑
└── parser.py      # Sitemap XML解析器
```

Sitemap爬虫的工作流程：
1. 获取配置的监控站点信息
2. 下载Sitemap XML文件
3. 解析XML获取URL列表
4. 与数据库中已存储的URL对比，找出新URL
5. 如配置需要，获取新URL的页面标题
6. 将新URL存入数据库
7. 触发飞书通知

#### 3.1.2 局部爬虫

```
app/scrapers/partial/
├── run.py         # 主入口
├── crawler.py     # 核心爬取逻辑
└── extractor.py   # 链接提取器
```

局部爬虫的工作流程：
1. 获取配置的监控站点信息
2. 下载指定的入口页面
3. 使用配置的CSS选择器或XPath提取链接
4. 与数据库中已存储的URL对比
5. 将新URL存入数据库
6. 触发飞书通知

#### 3.1.3 全站爬虫

```
app/scrapers/full/
├── run.py         # 主入口
├── crawler.py     # 核心爬取逻辑
└── robots.py      # robots.txt解析器
```

全站爬虫的工作流程：
1. 获取配置的监控站点信息
2. 如配置需要，解析robots.txt
3. 从基础URL开始递归爬取
4. 根据配置的深度限制和包含/排除规则过滤URL
5. 与数据库中已存储的URL对比
6. 将新URL存入数据库
7. 触发飞书通知

### 3.2 数据库操作模块

```
app/database/
├── connection.py  # 数据库连接管理
└── operations.py  # 数据库操作函数
```

主要功能：
- 连接PostgreSQL数据库
- 提供CRUD操作
- 事务管理
- 数据库迁移支持

### 3.3 通知模块

```
app/notifiers/
├── feishu.py      # 飞书通知实现
└── base.py        # 通知基类（便于扩展）
```

飞书通知功能：
- 构建通知消息
- 调用飞书Webhook API
- 错误重试机制
- 格式化消息内容

### 3.4 配置模块

```
app/config/
├── settings.py    # 全局配置
└── logging.py     # 日志配置
```

配置项包括：
- 数据库连接信息
- 爬虫默认设置
- 通知服务配置
- 日志级别和格式

### 3.5 工具模块

```
app/utils/
├── url.py         # URL处理函数
├── http.py        # HTTP请求工具
└── time.py        # 时间处理工具
```

提供各种辅助功能：
- URL标准化和解析
- HTTP请求封装
- 异常处理
- 时间处理

## 4. GitHub Actions配置

### 4.1 定时任务

```yaml
# .github/workflows/scheduled_crawl.yml
name: Scheduled Website Monitoring

on:
  schedule:
    # 每小时运行一次
    - cron: '0 * * * *'
  workflow_dispatch:
    inputs:
      site_id:
        description: '指定要监控的站点ID'
        required: false

jobs:
  crawl-sites:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
          
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          
      - name: Run crawler
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          FEISHU_WEBHOOK_URL: ${{ secrets.FEISHU_WEBHOOK_URL }}
        run: |
          if [ -z "${{ github.event.inputs.site_id }}" ]; then
            python -m app.scripts.run_all_active_sites
          else
            python -m app.scripts.run_specific_site ${{ github.event.inputs.site_id }}
          fi
```

## 5. 错误处理策略

### 5.1 异常处理

- 使用Python的`try-except`机制捕获异常
- 对网络请求设置超时和重试
- 记录详细错误日志
- 异常分级：致命错误（终止执行）和非致命错误（继续执行）
- 自动发送错误报告（严重错误）

### 5.2 日志记录

- 使用Python的`logging`模块
- 日志分级：DEBUG, INFO, WARNING, ERROR, CRITICAL
- 日志输出到控制台和文件
- 定期日志轮换
- 敏感信息脱敏（如API密钥）

## 6. 安全考虑

### 6.1 数据安全

- 环境变量存储敏感信息
- 使用GitHub Secrets存储密钥
- 数据库连接密码加密
- 数据库访问限制

### 6.2 爬虫礼仪

- 遵循robots.txt规则
- 控制爬取频率
- 设置合理的User-Agent
- 避免对目标服务器造成过大负载

## 7. 性能优化

### 7.1 爬虫优化

- 使用异步请求（aiohttp）提高并发
- 实现请求缓存机制
- 增量爬取，只处理变化部分
- 资源限制控制（内存、CPU使用）

### 7.2 数据库优化

- 索引优化
- 批量操作
- 连接池管理
- 查询优化

## 8. 扩展性设计

### 8.1 插件系统

计划实现插件系统，支持：
- 自定义解析器
- 自定义通知渠道
- 自定义数据处理流程

### 8.2 API设计

RESTful API设计：
- `/api/sites` - 监控站点管理
- `/api/pages` - 已发现页面查询
- `/api/logs` - 爬取日志查询
- 支持过滤、排序和分页

## 9. 测试策略

### 9.1 单元测试

- 使用`pytest`框架
- 测试覆盖率目标：>80%
- 模拟外部依赖（如HTTP请求、数据库）

### 9.2 集成测试

- 测试完整工作流程
- 使用测试数据库
- 测试真实场景

### 9.3 模拟网站

创建模拟网站用于测试：
- 具有Sitemap的网站
- 具有复杂HTML结构的网站
- 具有robots.txt限制的网站

## 10. 部署和运维

### 10.1 环境准备

- 创建PostgreSQL数据库实例
- 设置GitHub仓库
- 配置GitHub Actions权限
- 创建飞书机器人

### 10.2 监控和报警

- GitHub Actions运行状态监控
- 数据库连接监控
- 爬虫执行时间监控
- 错误率监控 