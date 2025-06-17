"""
Sitemap解析器模块，用于解析网站的Sitemap XML文件。
"""
import gzip
import time
from datetime import datetime
from io import BytesIO
from typing import Dict, List, Optional, Tuple, Set
from urllib.parse import urljoin

import requests
from loguru import logger
from lxml import etree

from app.utils.http import make_request
from app.utils.time import parse_iso_datetime


class SitemapParser:
    """
    Sitemap解析器，用于解析网站的Sitemap XML文件。
    """
    
    def __init__(
        self,
        user_agent: Optional[str] = None,
        proxy: Optional[str] = None,
        timeout: int = 30
    ):
        """
        初始化Sitemap解析器。
        
        Args:
            user_agent: 用户代理字符串
            proxy: 代理服务器URL
            timeout: 请求超时时间（秒）
        """
        self.user_agent = user_agent
        self.proxy = proxy
        self.timeout = timeout
    
    def fetch_sitemap(self, sitemap_url: str) -> Optional[bytes]:
        """
        获取Sitemap XML内容。
        
        Args:
            sitemap_url: Sitemap URL
            
        Returns:
            Optional[bytes]: Sitemap XML内容，如果获取失败则返回None
        """
        print(f">>> 正在获取Sitemap: {sitemap_url}")
        start_time = time.time()
        
        try:
            response = make_request(
                url=sitemap_url,
                user_agent=self.user_agent,
                proxy=self.proxy,
                timeout=self.timeout
            )
            
            content = response.content
            
            # 如果是gzip压缩的，解压缩
            if response.headers.get("Content-Type") == "application/x-gzip" or sitemap_url.endswith(".gz"):
                print(">>> 检测到压缩的Sitemap，正在解压缩...")
                try:
                    content = gzip.decompress(content)
                except Exception as e:
                    print(f">>> 解压缩Sitemap失败: {sitemap_url} - {str(e)}")
                    return None
            
            elapsed = time.time() - start_time
            print(f">>> Sitemap获取成功，大小: {len(content)/1024:.1f} KB，耗时: {elapsed:.2f}秒")
            return content
            
        except Exception as e:
            elapsed = time.time() - start_time
            print(f">>> 获取Sitemap失败: {sitemap_url} - {str(e)}")
            return None
    
    def parse_sitemap_index(self, content: bytes, base_url: str) -> List[str]:
        """
        解析Sitemap索引文件，获取子Sitemap URL列表。
        
        Args:
            content: Sitemap索引XML内容
            base_url: 基础URL，用于处理相对URL
            
        Returns:
            List[str]: 子Sitemap URL列表
        """
        print(">>> 正在解析Sitemap索引文件...")
        
        try:
            # 解析XML
            root = etree.fromstring(content)
            
            # 查找命名空间
            nsmap = root.nsmap
            
            # 默认命名空间
            ns = nsmap.get(None, "http://www.sitemaps.org/schemas/sitemap/0.9")
            
            # 子Sitemap URL列表
            sitemap_urls = []
            
            # 查找所有<sitemap>标签
            sitemap_elements = root.xpath(f"//s:sitemap/s:loc/text()", namespaces={"s": ns})
            
            for sitemap in sitemap_elements:
                sitemap_url = str(sitemap).strip()
                # 处理相对URL
                if not sitemap_url.startswith(("http://", "https://")):
                    sitemap_url = urljoin(base_url, sitemap_url)
                sitemap_urls.append(sitemap_url)
            
            print(f">>> 从索引中找到 {len(sitemap_urls)} 个子Sitemap")
            return sitemap_urls
            
        except Exception as e:
            print(f">>> 解析Sitemap索引失败: {str(e)}")
            return []
    
    def parse_sitemap(self, content: bytes) -> List[Dict[str, str]]:
        """
        解析Sitemap文件，获取URL列表及其元数据。
        
        Args:
            content: Sitemap XML内容
            
        Returns:
            List[Dict[str, str]]: URL列表及其元数据（url, lastmod）
        """
        print(">>> 正在解析Sitemap文件...")
        
        try:
            # 解析XML
            root = etree.fromstring(content)
            
            # 查找命名空间
            nsmap = root.nsmap
            
            # 默认命名空间
            ns = nsmap.get(None, "http://www.sitemaps.org/schemas/sitemap/0.9")
            
            # URL列表
            url_entries = []
            
            # 查找所有<url>标签
            url_elements = root.xpath(f"//s:url", namespaces={"s": ns})
            url_count = len(url_elements)
            print(f">>> 在Sitemap中找到 {url_count} 个URL元素")
            
            # 如果URL太多，显示进度
            show_progress = url_count > 1000
            progress_step = max(1, url_count // 10)  # 显示10个进度点
            
            for i, url in enumerate(url_elements):
                # 显示进度
                if show_progress and i % progress_step == 0:
                    progress = (i / url_count) * 100
                    print(f">>> 解析进度: {progress:.1f}% ({i}/{url_count})")
                
                loc = url.xpath(f"s:loc/text()", namespaces={"s": ns})
                lastmod = url.xpath(f"s:lastmod/text()", namespaces={"s": ns})
                
                if loc:
                    url_entry = {
                        "url": str(loc[0]).strip()
                    }
                    
                    if lastmod:
                        url_entry["lastmod"] = str(lastmod[0]).strip()
                    
                    url_entries.append(url_entry)
            
            print(f">>> Sitemap文件解析完成，提取出 {len(url_entries)} 个有效URL")
            return url_entries
            
        except Exception as e:
            print(f">>> 解析Sitemap失败: {str(e)}")
            return []
    
    def is_sitemap_index(self, content: bytes) -> bool:
        """
        检查Sitemap内容是否是Sitemap索引文件。
        
        Args:
            content: Sitemap XML内容
            
        Returns:
            bool: 如果是Sitemap索引文件则返回True，否则返回False
        """
        try:
            # 解析XML
            root = etree.fromstring(content)
            
            # 检查根标签名称
            is_index = root.tag.endswith("sitemapindex")
            
            if is_index:
                print(">>> 检测到Sitemap索引文件")
            else:
                print(">>> 检测到常规Sitemap文件")
                
            return is_index
            
        except Exception as e:
            print(f">>> 检查Sitemap类型失败: {str(e)}")
            return False
    
    def fetch_and_parse_sitemap(self, sitemap_url: str, base_url: str) -> Tuple[List[Dict[str, str]], Set[str]]:
        """
        获取并解析Sitemap，支持递归解析Sitemap索引。
        
        Args:
            sitemap_url: Sitemap URL
            base_url: 基础URL，用于处理相对URL
            
        Returns:
            Tuple[List[Dict[str, str]], Set[str]]: URL列表及其元数据，以及处理过的Sitemap URL集合
        """
        print(f">>> 开始获取并解析Sitemap: {sitemap_url}")
        overall_start_time = time.time()
        
        processed_sitemaps = set()
        all_urls = []
        
        def process_sitemap(url, level=0):
            indent = "  " * level
            if url in processed_sitemaps:
                return
            
            processed_sitemaps.add(url)
            
            print(f">>> {indent}处理Sitemap({level+1}级): {url}")
            content = self.fetch_sitemap(url)
            
            if not content:
                print(f">>> {indent}无法获取Sitemap: {url}")
                return
            
            # 检查是否是Sitemap索引
            if self.is_sitemap_index(content):
                # 如果是Sitemap索引，递归处理所有子Sitemap
                child_sitemaps = self.parse_sitemap_index(content, base_url)
                
                for i, child_url in enumerate(child_sitemaps):
                    print(f">>> {indent}处理子Sitemap [{i+1}/{len(child_sitemaps)}]: {child_url}")
                    process_sitemap(child_url, level + 1)
            else:
                # 解析Sitemap URL
                urls = self.parse_sitemap(content)
                print(f">>> {indent}从Sitemap解析出 {len(urls)} 个URL")
                all_urls.extend(urls)
        
        process_sitemap(sitemap_url)
        
        overall_elapsed = time.time() - overall_start_time
        print(f">>> 所有Sitemap处理完成，总耗时: {overall_elapsed:.2f}秒")
        print(f">>> 处理了 {len(processed_sitemaps)} 个Sitemap，共找到 {len(all_urls)} 个URL")
        
        return all_urls, processed_sitemaps
    
    def extract_urls_from_sitemap(self, sitemap_url: str, base_url: str) -> List[Dict[str, str]]:
        """
        从Sitemap URL中提取所有URL。
        
        Args:
            sitemap_url: Sitemap URL
            base_url: 基础URL，用于处理相对URL
            
        Returns:
            List[Dict[str, str]]: URL列表及其元数据
        """
        all_urls, processed_sitemaps = self.fetch_and_parse_sitemap(sitemap_url, base_url)
        return all_urls 