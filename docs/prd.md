**需求文档：洞察先锋 (InsightPioneer) - 竞品网站页面监控系统**

**版本：** 1.3
**日期：** 2025-05-13
**来源：** https://g.co/gemini/share/6c0a0cedf643

**1. 项目概述与目标**

* **1.1 项目背景：**
    个人站长通过捕捉用户需求关键词开发网站并通过Google SEO获取流量变现。当前通过Google Trends挖掘关键词竞争激烈，效率不高。为抢占先机，需要第一时间发现并跟进竞争对手（尤其是敏锐的老网站）新上线的网页内容（如在线H5小游戏）。
* **1.2 项目目标：**
    开发一个网站监控系统，能够自动化地跟踪和监控指定网站的页面变化，特别是新发布页面的情况，以便用户能够快速响应，复制或开发类似内容，从而在SEO中获得时间优势。
* **1.3 核心价值：**
    * **快速发现：** 缩短新内容机会的发现时间。
    * **精准跟进：** 针对性地监控高价值竞争对手。
    * **效率提升：** 自动化监控，解放人力。
* **1.4 项目名称：**
    * **中文名：** 洞察先锋
    * **英文名：** InsightPioneer

**2. 用户画像与使用场景**

* **2.1 用户画像：**
    * 个人站长、SEO从业者、内容创作者。
    * 依赖Google自然流量。
    * 关注行业动态和竞争对手策略。
    * 具备一定的技术理解能力或愿意使用工具辅助。
* **2.2 使用场景：**
    * **场景一：监控H5小游戏网站**
        用户A配置监控某知名在线H5小游戏网站 `example-games.com`。当该网站新上线一款名为 "Super Flight Adventure" 的游戏页面 (`example-games.com/games/super-flight-adventure`) 时，系统应能及时发现此新页面，并通知用户A。用户A随即快速开发或上线同款/类似游戏。
    * **场景二：监控行业资讯/博客网站**
        用户B监控某行业头部博客 `industry-leader-blog.com` 的 "最新文章" 或 "热门趋势" 板块。当该板块出现指向新文章的链接时，系统记录新文章URL，用户B可快速了解行业新动态并创作相关内容。
    * **场景三：监控电商网站新品**
        用户C监控某竞争对手电商网站 `competitor-store.com` 的 "新品上架" 类目页面。当该类目下出现新的商品链接时，系统捕获并通知用户C。

**3. 功能需求 (Functional Requirements)**

* **3.1 监控配置管理 (Configuration Management)**
    * **FR3.1.1 添加监控网站：**
        * 输入目标网站名称（备注用）。
        * 输入目标网站的基础URL (e.g., `https://www.example.com`)。
        * 选择监控方式（Sitemap监控、全站爬取、局部爬取）。
        * 配置监控频率（如：每1小时、每6小时、每天等）。
        * (可选) 配置User-Agent。
        * (可选) 配置代理服务器。
        * (可选) 配置是否为通过Sitemap发现的新URL获取标题 (0=不获取, 1=获取)。
    * **FR3.1.2 Sitemap监控配置：**
        * 若选择Sitemap监控，需指定Sitemap URL。
        * **示例：**
            * **网站：** `https://www.a.com` (假设其sitemap在 `https://www.a.com/sitemap.xml`)
            * **监控方式：** Sitemap监控
            * **Sitemap URL：** `https://www.a.com/sitemap.xml`
            * **为Sitemap发现URL获取标题：** 1 (是)
    * **FR3.1.3 全站爬取配置：**
        * (可选) 设置爬取深度限制 (例如：3层)。
        * (可选) 设置爬取并发数 (例如：2)。
        * (可选) 设置爬取间隔（ polite crawling, 例如：1秒）。
        * (可选) 遵循 `robots.txt` (可配置是否强制遵守，0=不遵守, 1=遵守)。
        * (可选) URL包含/排除规则（使用正则表达式或关键词）。
        * **示例：**
            * **网站：** `https://www.b.com`
            * **监控方式：** 全站爬取
            * **爬取深度：** 5
            * **遵循robots.txt：** 1 (是)
            * **URL包含规则：** `/products/` (只爬取产品相关的页面)
    * **FR3.1.4 局部爬取配置：**
        * 指定入口页面URL(s)（如类目页、热门列表页）。
        * 指定用于提取目标链接的CSS选择器或XPath表达式。
        * (可选) 配置是否跟踪分页（如果列表有分页，可能需要更复杂的逻辑或多个选择器）。
        * **示例 (监控某个游戏网站的“热门游戏”板块)：**
            * **网站：** `https://game-world.com`
            * **监控方式：** 局部爬取
            * **入口页面URL：** `https://game-world.com/hot-games`
            * **CSS选择器 (提取游戏详情页链接)：** `div.hot-game-list ul li a`
            * **CSS选择器 (提取游戏标题，可选，若不配置则爬虫会尝试从链接目标页获取`<title>`标签)：** `div.hot-game-list ul li a span.game-title`
    * **FR3.1.5 编辑监控配置：** 允许修改已添加网站的各项配置。
    * **FR3.1.6 删除监控配置：** 允许删除不再需要监控的网站。
    * **FR3.1.7 启用/禁用监控：** 0=禁用, 1=启用。

* **3.2 监控执行与数据采集 (Monitoring Execution & Data Collection)**
    * **FR3.2.1 任务调度器：**
        * **方案：GitHub Actions**。使用 GitHub Actions 的 scheduled events (cron) 定期触发Python爬虫脚本。
    * **FR3.2.2 Sitemap解析器：**
        * 获取并解析Sitemap文件（XML格式）。
        * 提取Sitemap中所有URL及其`<lastmod>` (若有)。
    * **FR3.2.3 网页爬虫 (Full & Partial)：**
        * **链接发现：** 根据配置（全站或局部规则）爬取网页，提取页面中的`<a>`标签的`href`属性。
        * **链接规范化：** 将相对URL转换为绝对URL。
        * **链接过滤：** 过滤掉非HTTP/HTTPS链接、站外链接（除非特别配置）、以及已配置的排除规则。
    * **FR3.2.4 页面标题获取 (Page Title Extraction):**
        * 对于爬虫监控（全站/局部），在爬取页面时，尝试提取`<title>`标签内容。
        * 对于Sitemap监控，如果配置为获取标题 (FR3.1.1)，则对新发现的URL发起HTTP GET请求以获取HTML并提取`<title>`标签。若未配置或获取失败，`page_title`可为空。
    * **FR3.2.5 数据去重与更新：**
        * 对于每个监控的网站，将本次采集到的URL列表与数据库中已存储的该网站的URL列表进行比较。
        * 新发现的URL作为新记录插入。
        * 已存在的URL更新“最后采集时间”或“最后活跃时间”。

* **3.3 数据存储 (Data Storage)**
    * **FR3.3.1 数据库：PostgreSQL** (云托管，如 Neon, Supabase, Aiven, AWS RDS for PostgreSQL, Google Cloud SQL for PostgreSQL)。
    * **FR3.3.2 监控配置数据：** 存储FR3.1中用户配置的监控网站信息 (见下方数据模型)。
    * **FR3.3.3 采集页面数据：** (见下方数据模型)。

* **3.4 结果展示与通知 (Results Display & Notification)**
    * **FR3.4.1 仪表盘 (Dashboard)：**
        * 概览：显示监控中的网站总数、今日新发现页面总数等。
    * **FR3.4.2 新页面列表：**
        * 按时间倒序列出所有新发现的页面。
        * 包含信息：所属监控网站、页面URL、页面标题（若有）、发现时间。
        * 提供筛选功能：按监控网站筛选、按日期范围筛选。
        * 提供直接打开URL的链接。
    * **FR3.4.3 监控网站详情：**
        * 点击某个监控网站，可查看该网站下所有已发现的页面列表。
        * 显示该网站的监控配置信息。
        * (可选) 显示该网站的监控历史/日志。
    * **FR3.4.4 飞书机器人通知：**
        * 当发现新页面时，通过调用飞书机器人Webhook API发送通知。
        * 通知内容应包含：新页面的URL、所属监控网站的名称、页面标题（若有）、发现时间。
        * 可配置是否启用通知 (针对每个监控网站或全局)。
    * **FR3.4.5 标记已处理：** `is_processed` 字段 (0=未处理, 1=已处理)。

* **3.5 系统管理 (System Administration)**
    * **FR3.5.1 用户认证：** 初期可简化。
    * **FR3.5.2 任务管理 (通过GitHub Actions查看)：** GitHub Actions界面提供任务执行历史、日志、状态。
    * **FR3.5.3 手动触发监控 (通过GitHub Actions)：** 可以通过GitHub Actions的 `workflow_dispatch` 事件手动触发某个监控工作流程。

**4. 非功能性需求 (Non-Functional Requirements)**

* **NF4.1 性能 (Performance)：**
    * GitHub Actions有执行时间限制，单个爬取任务应设计为在该限制内完成，或分解为更小的任务。
    * 前端页面在Vercel上应有良好的加载速度。
* **NF4.2 可靠性 (Reliability)：**
    * Python脚本应有健壮的错误处理（网络超时、HTTP错误、解析错误）。
    * 数据库连接的可靠性依赖于所选的云数据库服务。
* **NF4.3 易用性 (Usability)：** 配置界面应简洁直观，结果展示清晰。
* **NF4.4 资源消耗 (Resource Consumption)：** 合理控制爬取过程中的CPU、内存和网络带宽消耗，遵守爬虫礼仪。
* **NF4.5 可维护性 (Maintainability)：**
    * **代码结构：** 后端 (Python Scrapers & GitHub Actions workflows) 和 前端 (Next.js + TailwindCSS) 分别使用独立的GitHub项目。
    * 清晰的模块化设计。
* **NF4.6 可扩展性 (Scalability)：** 数据库 Schema 设计考虑未来可能的字段增加。
* **NF4.7 数据准确性 (Data Accuracy)：** 确保URL提取和识别的准确性。
* **NF4.8 部署架构 (Deployment Architecture)：**
    * **前端：** Next.js应用部署在Vercel。
    * **后端逻辑 (爬虫)：** Python脚本，通过GitHub Actions按计划执行。
    * **数据库：** 云托管的PostgreSQL服务。
    * **API层 (可选)：** Next.js的API Routes (Serverless Functions on Vercel) 可以作为前端与数据库交互的中间层。

**5. 数据模型 (PostgreSQL Schema)**

* **`monitored_sites` (监控站点表)**
    * `id` (SERIAL PRIMARY KEY)
    * `name` (VARCHAR(255), NOT NULL)
    * `base_url` (VARCHAR(2048), NOT NULL)
    * `monitoring_type` (VARCHAR(50), NOT NULL CHECK (`monitoring_type` IN ('sitemap', 'full_crawl', 'partial_crawl')))
    * `sitemap_url` (VARCHAR(2048))
    * `crawl_config_json` (JSONB) -- *存储特定于爬取方式的配置*
        * *示例 (全站爬取): `{"depth_limit": 3, "respect_robots_txt": 1, "include_patterns": ["/products/"], "exclude_patterns": ["/archive/"]}`*
        * *示例 (局部爬取): `{"entry_page_url": "https://example.com/news", "link_selector": "article.news-item a.title-link", "title_selector_override": "article.news-item a.title-link h3"}`*
    * `monitoring_frequency_minutes` (INTEGER, NOT NULL DEFAULT 1440)
    * `user_agent` (VARCHAR(255))
    * `proxy_config_json` (JSONB)
    * `Workspace_title_for_sitemap_urls` (SMALLINT, NOT NULL DEFAULT 1) -- *0 for false, 1 for true. For sitemap monitoring.*
    * `is_enabled` (SMALLINT, NOT NULL DEFAULT 1) -- *0 for false, 1 for true*
    * `is_notification_enabled` (SMALLINT, NOT NULL DEFAULT 1) -- *0 for false, 1 for true, for Feishu notifications*
    * `last_crawled_at` (TIMESTAMP WITH TIME ZONE)
    * `created_at` (TIMESTAMP WITH TIME ZONE, NOT NULL DEFAULT CURRENT_TIMESTAMP)
    * `updated_at` (TIMESTAMP WITH TIME ZONE, NOT NULL DEFAULT CURRENT_TIMESTAMP)

* **`discovered_pages` (已发现页面表)**
    * `id` (SERIAL PRIMARY KEY)
    * `monitored_site_id` (INTEGER, NOT NULL, REFERENCES `monitored_sites`(`id`) ON DELETE CASCADE)
    * `url` (TEXT, NOT NULL)
    * `page_title` (TEXT) -- *可能为空, 特别是Sitemap监控且未配置获取标题时*
    * `first_discovered_at` (TIMESTAMP WITH TIME ZONE, NOT NULL DEFAULT CURRENT_TIMESTAMP)
    * `last_seen_at` (TIMESTAMP WITH TIME ZONE, NOT NULL DEFAULT CURRENT_TIMESTAMP) -- *更新于每次检查时发现该URL仍存在*
    * `is_processed` (SMALLINT, NOT NULL DEFAULT 0) -- *0 for false, 1 for true*
    * UNIQUE (`monitored_site_id`, `url`)

* **`crawl_logs` (爬取日志表 - 可选)**
    * `id` (SERIAL PRIMARY KEY)
    * `monitored_site_id` (INTEGER, NOT NULL, REFERENCES `monitored_sites`(`id`) ON DELETE CASCADE)
    * `run_id` (VARCHAR(255)) -- *GitHub Actions run ID, for traceability*
    * `start_time` (TIMESTAMP WITH TIME ZONE, NOT NULL)
    * `end_time` (TIMESTAMP WITH TIME ZONE)
    * `status` (VARCHAR(50), NOT NULL CHECK (`status` IN ('success', 'partial_success', 'failed')))
    * `pages_found_count` (INTEGER, DEFAULT 0)
    * `message` (TEXT)
    * `created_at` (TIMESTAMP WITH TIME ZONE, NOT NULL DEFAULT CURRENT_TIMESTAMP)

**6. 技术栈 (Technology Stack)**

* **后端 (爬虫与计划任务)：**
    * Python (使用 Requests, BeautifulSoup4/lxml, psycopg2-binary 操作 PostgreSQL)
    * GitHub Actions (用于调度和执行)
* **数据库：** PostgreSQL (云托管，例如 Neon, Supabase, Aiven, ElephantSQL)
* **前端 (管理界面与API层)：**
    * Next.js (React 框架)
    * Tailwind CSS
    * 部署平台: Vercel
* **通知服务：** 飞书机器人 (通过 Webhook)

**7. 项目结构 (GitHub Repositories)**

* **代码库 1: `insightpioneer-scrapers` (或 `insightpioneer-backend`)**
    * 包含用于Sitemap解析、全站爬取、局部爬取的Python脚本。
    * 数据库交互逻辑。
    * 飞书通知逻辑。
    * `.github/workflows/` 目录，存放GitHub Actions的YAML配置文件 (用于计划任务和手动触发)。
* **代码库 2: `insightpioneer-frontend` (或 `insightpioneer-ui`)**
    * Next.js 应用。
    * 用于配置监控站点、查看已发现页面的页面。
    * API路由 (如果需要) 用于与数据库交互，并按需进行保护。

**8. 部署与运维 (Deployment & Operations)**

* **数据库：** 在云服务提供商上设置一个托管的PostgreSQL实例。保护好凭据和连接字符串。
* **后端爬虫：**
    * 将数据库凭据和飞书Webhook URL作为GitHub Secrets存储在 `insightpioneer-scrapers` 代码库中。
    * 配置GitHub Actions工作流程以按计划运行 (例如，每小时、每天)。
    * 工作流程将检出代码，安装Python依赖，并运行爬虫脚本。
* **前端：**
    * 将Next.js应用程序部署到Vercel。
    * 在Vercel中配置环境变量，用于数据库连接 (如果前端API路由直接访问数据库) 以及任何API密钥。
    * 如果使用API路由，这些将是由Vercel管理的Serverless Functions。

**9. 迭代计划 (Iteration Plan - 建议)**

* **MVP (最小可行产品) 阶段一：核心监控与发现 (聚焦Sitemap)**
    * **后端：** 实现Sitemap监控的Python脚本，将结果存储在PostgreSQL中。设置GitHub Action来运行它。为新页面添加飞书通知功能。提供选项来决定是否为Sitemap发现的URL获取标题。
    * **前端：** 构建基础的Next.js用户界面，允许手动向数据库添加站点 (Sitemap URL, 频率, 是否获取标题选项)，并列出从数据库中新发现的页面。
    * 手动设置数据库。
* **MVP 阶段二：增强监控 (局部爬取) 与UI优化**
    * **后端：** 添加局部爬取的Python脚本。
    * **前端：** 增强用户界面以支持局部爬取的配置 (入口URL, CSS选择器)。改进已发现页面的显示。
* **后续迭代：**
    * 实现全站爬取功能。
    * 增加高级配置选项 (User-Agent, 代理, 爬取深度限制)。
    * 在用户界面中实现“已处理”标记 (`is_processed`) 的功能。
    * 实现并展示 `crawl_logs` (爬取日志) 表。
    * 更稳健的错误处理和报告机制。
