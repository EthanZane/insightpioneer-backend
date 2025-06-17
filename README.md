# 洞察先锋 (InsightPioneer)

## 项目概述

洞察先锋是一个自动化网站监控系统，专为个人站长、SEO从业者和内容创作者设计。该系统能够自动跟踪和监控指定网站的页面变化，特别是新发布页面的情况，帮助用户快速响应市场变化，抢占先机。

### 核心价值
- **快速发现**：第一时间发现竞争对手的新内容
- **精准跟进**：针对性地监控高价值目标网站
- **效率提升**：自动化监控，解放人力资源

## 技术架构

### 后端 (本仓库)
- **编程语言**：Python
- **主要库**：Requests, BeautifulSoup4/lxml, psycopg2-binary
- **调度系统**：GitHub Actions
- **数据库**：PostgreSQL (云托管)
- **通知服务**：飞书机器人 (Webhook)

### 前端 (独立仓库)
- **框架**：Next.js (React)
- **样式**：Tailwind CSS
- **部署平台**：Vercel

## 功能概述

1. **多种监控模式**
   - Sitemap监控：通过解析网站的Sitemap XML发现新页面
   - 局部爬取：监控特定页面上的链接变化
   - 全站爬取：对整个网站进行深度抓取

2. **灵活配置**
   - 监控频率通过GitHub Actions的cron配置控制
   - 可选User-Agent和代理配置
   - 支持URL包含/排除规则

3. **结果展示**
   - 实时仪表盘
   - 新页面列表
   - 监控网站详情

4. **通知机制**
   - 飞书机器人及时通知新发现的页面

## 目录结构

```
insightpioneer-backend/
├── app/                    # 核心应用代码
│   ├── config/             # 配置文件
│   ├── models/             # 数据模型
│   ├── scrapers/           # 爬虫模块
│   │   ├── sitemap/        # Sitemap解析器
│   │   ├── partial/        # 局部爬取
│   │   └── full/           # 全站爬取
│   ├── database/           # 数据库操作
│   ├── notifiers/          # 通知服务
│   └── utils/              # 工具函数
├── scripts/                # 辅助脚本
├── tests/                  # 测试代码
└── .github/workflows/      # GitHub Actions配置
```

## 环境变量

项目需要以下环境变量：

```
DATABASE_URL=postgresql://username:password@host:port/database
FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/your-webhook-id
FEISHU_SECRET=your-feishu-bot-secret-key
```

## 开发指南

### 环境设置

1. 克隆仓库
```bash
git clone https://github.com/your-username/insightpioneer-backend.git
cd insightpioneer-backend
```

2. 创建并激活虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # 在Windows上使用 venv\Scripts\activate
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

4. 创建环境变量配置文件
在项目根目录创建一个`.env`文件，添加以下内容：
```
DATABASE_URL=postgresql://username:password@host:port/database
FEISHU_WEBHOOK_URL=https://open.feishu.cn/open-apis/bot/v2/hook/your-webhook-id
FEISHU_SECRET=your-feishu-bot-secret-key
```

5. 配置数据库连接
   - **本地PostgreSQL**：安装PostgreSQL，创建名为`insightpioneer`的数据库，然后更新`.env`中的连接字符串为：
     ```
     DATABASE_URL=postgresql://localhost:5432/insightpioneer
     ```
   - **云数据库**：从Supabase、Neon等PostgreSQL云服务获取连接字符串并更新`.env`

6. 初始化数据库
```bash
python scripts/init_database.py
```

7. 创建测试数据
如果数据库初始化成功但看不到表或需要添加测试数据：
```bash
python scripts/create_test_site.py
```
这将创建一个用于测试的监控站点配置。

8. 配置飞书通知（可选）
   - 登录飞书管理后台
   - 进入"应用管理" -> "自建应用" -> "创建应用"
   - 添加机器人功能，选择"群机器人"
   - 获取Webhook URL并更新`.env`文件

### 添加测试站点

可以通过以下SQL添加一个测试站点：

```sql
INSERT INTO monitored_sites (
    name, base_url, monitoring_type, sitemap_url, 
    fetch_title_for_sitemap_urls,
    is_enabled, is_notification_enabled
) VALUES (
    '测试站点', 'https://example.com', 'sitemap',
    'https://example.com/sitemap.xml', 1, 1, 1
);
```

### 运行测试

```bash
pytest
```

## 运行脚本说明

本项目提供了多种脚本来运行站点监控任务，以下是详细的使用说明：

### 1. 直接运行Sitemap爬虫

```bash
python -m app.scrapers.sitemap.run --config-id=<站点ID> [选项]
```

**必选参数：**
- `--config-id=<站点ID>` - 指定要监控的站点ID（必须是数据库中已存在的站点ID）

**可选参数：**
- `--no-title` - 不获取页面标题（默认会获取标题）
- `--no-notify` - 不发送飞书通知（默认会发送通知）

**示例：**
```bash
# 基本用法 - 运行ID为1的站点监控
python -m app.scrapers.sitemap.run --config-id=1

# 不获取标题
python -m app.scrapers.sitemap.run --config-id=1 --no-title

# 不发送通知
python -m app.scrapers.sitemap.run --config-id=1 --no-notify

# 同时不获取标题且不发送通知
python -m app.scrapers.sitemap.run --config-id=1 --no-title --no-notify
```

### 2. 运行特定站点（自动选择爬虫类型）

```bash
python scripts/run_specific_site.py <站点ID> [选项]
```

**必选参数：**
- `<站点ID>` - 指定要监控的站点ID（必须是数据库中已存在且已启用的站点ID）

**可选参数：**
- `--no-title` - 不获取页面标题（默认会获取标题）
- `--no-notify` - 不发送飞书通知（默认会发送通知）

**注意事项：**
- 此脚本会先检查站点是否存在且已启用，然后根据站点的`monitoring_type`自动选择合适的爬虫
- 目前只实现了Sitemap爬虫，局部爬取和全站爬取功能尚未实现

**示例：**
```bash
# 基本用法 - 运行ID为1的站点监控
python scripts/run_specific_site.py 1

# 不获取标题
python scripts/run_specific_site.py 1 --no-title

# 不发送通知
python scripts/run_specific_site.py 1 --no-notify
```

### 3. 运行所有需要执行的站点

```bash
python scripts/run_all_active_sites.py
```

**说明：**
- 此脚本会自动运行所有已启用的站点
- 不需要任何参数，系统会自动选择站点和爬虫类型
- 监控频率通过GitHub Actions的cron配置控制，而不是通过数据库中的配置

### 4. 数据库初始化脚本

```bash
python scripts/init_database.py [--force]
```

**可选参数：**
- `--force` - 强制重新创建表（危险操作，会删除所有数据）

### 5. 创建测试站点

```bash
python scripts/create_test_site.py
```

**说明：**
- 此脚本会创建一个默认的测试站点配置
- 不需要任何参数

### 6. 测试飞书通知

```bash
# 发送测试通知
python -c "from app.notifiers.feishu import FeishuNotifier; FeishuNotifier().send_test_notification()"
```

**注意事项：**
- 飞书机器人必须配置签名校验才能正常使用
- 确保`.env`文件中正确设置了`FEISHU_WEBHOOK_URL`和`FEISHU_SECRET`
- 如果测试失败，请检查环境变量是否正确

## 脚本用法对比说明

1. **`app.scrapers.sitemap.run` vs `run_specific_site.py`**
   - 如果您确定要运行的是Sitemap类型的站点，可以直接使用`app.scrapers.sitemap.run`
   - 如果您不确定站点类型或希望有更多验证，建议使用更通用的`run_specific_site.py`脚本

2. **单站点运行 vs 批量运行**
   - 对于测试或特定需求，使用`run_specific_site.py`运行单个站点
   - 对于定期监控，使用`run_all_active_sites.py`自动运行所有启用的站点，配合GitHub Actions的cron配置控制执行频率

## 部署指南

1. 在GitHub Secrets中设置环境变量
   - 进入GitHub仓库设置 -> Secrets and variables -> Actions
   - 添加`DATABASE_URL`、`FEISHU_WEBHOOK_URL`和`FEISHU_SECRET`密钥

2. 配置GitHub Actions工作流程
   - 工作流程配置已在`.github/workflows/scheduled_crawl.yml`中定义
   - 通过修改yml文件中的cron表达式来调整监控频率

3. 设置云数据库
   - 确保数据库允许GitHub Actions的IP地址访问

4. 部署前端应用到Vercel

## 使用指南

详细的使用说明请参考 [使用文档](docs/usage.md)。

## 开发路线图

### MVP阶段一：核心监控与发现 (聚焦Sitemap)
- [x] 搭建基础项目结构
- [ ] 实现数据库模型
- [ ] 开发Sitemap监控脚本
- [ ] 配置GitHub Actions调度
- [ ] 实现飞书通知功能

### MVP阶段二：增强监控 (局部爬取) 与优化
- [ ] 实现局部爬取功能
- [ ] 增强错误处理
- [ ] 优化监控性能

### 后续迭代
- [ ] 实现全站爬取功能
- [ ] 高级配置选项 (User-Agent, 代理, 爬取深度限制)
- [ ] 实现爬取日志功能
- [ ] 更多通知渠道支持
- [ ] 用户认证系统

## 贡献指南

欢迎贡献！请查看 [贡献指南](CONTRIBUTING.md) 了解如何参与项目开发。

## 许可证

[MIT](LICENSE)

## 监控类型配置说明

系统支持三种不同的监控类型，每种类型需要配置不同的参数：

### 1. Sitemap 监控 (monitoring_type = 'sitemap')

这种监控方式通过解析网站的Sitemap XML文件来发现网站页面。适用于有规范Sitemap的站点。

**必填字段：**
- `name`: 站点名称，如"示例网站"
- `base_url`: 站点基础URL，如"https://example.com"
- `monitoring_type`: 必须设置为"sitemap"
- `sitemap_url`: Sitemap的完整URL，如"https://example.com/sitemap.xml"

**可选字段：**
- `fetch_title_for_sitemap_urls`: 是否获取页面标题，1=是(默认)，0=否
- `is_enabled`: 是否启用此监控，1=是(默认)，0=否
- `is_notification_enabled`: 是否启用通知，1=是(默认)，0=否
- `user_agent`: 自定义User-Agent字符串
- `proxy_config_json`: 代理配置，JSON格式，例如：
  ```json
  {
    "http": "http://user:pass@10.10.1.10:3128/",
    "https": "https://user:pass@10.10.1.10:3128/"
  }
  ```

**示例SQL：**
```sql
INSERT INTO monitored_sites (
    name, base_url, monitoring_type, sitemap_url, 
    fetch_title_for_sitemap_urls, 
    is_enabled, is_notification_enabled
) VALUES (
    'Example.com', 'https://example.com', 'sitemap',
    'https://example.com/sitemap.xml',
    1, 1, 1
);
```

### 2. 局部爬取 (monitoring_type = 'partial_crawl')

这种监控方式仅爬取指定页面及其直接链接的页面。适用于只需监控特定区域的站点。

**必填字段：**
- `name`: 站点名称
- `base_url`: 站点基础URL
- `monitoring_type`: 必须设置为"partial_crawl"
- `crawl_config_json`: 爬取配置，JSON格式，必须包含：
  ```json
  {
    "start_urls": ["https://example.com/page1", "https://example.com/page2"],
    "include_patterns": ["https://example.com/.*"],
    "exclude_patterns": [".*\\?(utm|ref)=.*"],
    "max_depth": 1
  }
  ```

**可选字段：**
- `is_enabled`: 是否启用此监控，1=是(默认)，0=否
- `is_notification_enabled`: 是否启用通知，1=是(默认)，0=否
- `user_agent`: 自定义User-Agent字符串
- `proxy_config_json`: 代理配置，JSON格式

**示例SQL：**
```sql
INSERT INTO monitored_sites (
    name, base_url, monitoring_type, 
    crawl_config_json,
    is_enabled, is_notification_enabled
) VALUES (
    'Example Blog', 'https://example.com/blog', 'partial_crawl',
    '{"start_urls": ["https://example.com/blog"], "include_patterns": ["https://example.com/blog/.*"], "exclude_patterns": [".*\\?(utm|ref)=.*"], "max_depth": 1}',
    1, 1
);
```

### 3. 全站爬取 (monitoring_type = 'full_crawl')

这种监控方式会递归爬取整个网站。适用于需要全面监控且没有Sitemap的小型站点。

**必填字段：**
- `name`: 站点名称
- `base_url`: 站点基础URL（爬取起点）
- `monitoring_type`: 必须设置为"full_crawl"
- `crawl_config_json`: 爬取配置，JSON格式，必须包含：
  ```json
  {
    "include_patterns": ["https://example.com/.*"],
    "exclude_patterns": [".*\\?(utm|ref)=.*", ".*/tag/.*", ".*/category/.*"],
    "max_depth": 3,
    "max_pages": 1000
  }
  ```

**可选字段：**
- `is_enabled`: 是否启用此监控，1=是(默认)，0=否
- `is_notification_enabled`: 是否启用通知，1=是(默认)，0=否
- `user_agent`: 自定义User-Agent字符串
- `proxy_config_json`: 代理配置，JSON格式

**示例SQL：**
```sql
INSERT INTO monitored_sites (
    name, base_url, monitoring_type, 
    crawl_config_json,
    is_enabled, is_notification_enabled
) VALUES (
    'Small Blog', 'https://smallblog.com', 'full_crawl',
    '{"include_patterns": ["https://smallblog.com/.*"], "exclude_patterns": [".*\\?(utm|ref)=.*", ".*/tag/.*"], "max_depth": 3, "max_pages": 500}',
    1, 1
);
```

### 快速添加站点的脚本示例

如果不想手写SQL，可以使用以下Python脚本添加站点：

```python
# 添加Sitemap监控站点
python -c "from app.models.site import MonitoredSite; from app.database.session import db_session; site = MonitoredSite(name='Example.com', base_url='https://example.com', monitoring_type='sitemap', sitemap_url='https://example.com/sitemap.xml', fetch_title_for_sitemap_urls=1, is_enabled=1, is_notification_enabled=1); db_session.add(site); db_session.commit()"

# 添加局部爬取监控站点
python -c "from app.models.site import MonitoredSite; from app.database.session import db_session; import json; crawl_config = {'start_urls': ['https://example.com/blog'], 'include_patterns': ['https://example.com/blog/.*'], 'exclude_patterns': ['.*\\\\?(utm|ref)=.*'], 'max_depth': 1}; site = MonitoredSite(name='Example Blog', base_url='https://example.com/blog', monitoring_type='partial_crawl', crawl_config_json=json.dumps(crawl_config), is_enabled=1, is_notification_enabled=1); db_session.add(site); db_session.commit()"

# 添加全站爬取监控站点
python -c "from app.models.site import MonitoredSite; from app.database.session import db_session; import json; crawl_config = {'include_patterns': ['https://smallblog.com/.*'], 'exclude_patterns': ['.*\\\\?(utm|ref)=.*', '.*/tag/.*'], 'max_depth': 3, 'max_pages': 500}; site = MonitoredSite(name='Small Blog', base_url='https://smallblog.com', monitoring_type='full_crawl', crawl_config_json=json.dumps(crawl_config), is_enabled=1, is_notification_enabled=1); db_session.add(site); db_session.commit()"
```

## 使用指南

详细的使用说明请参考 [使用文档](docs/usage.md)。