"""
URL处理工具模块，提供URL处理相关功能。
"""
import re
from typing import Optional, Set, List
from urllib.parse import urljoin, urlparse, urlunparse, ParseResult


def normalize_url(url: str, base_url: Optional[str] = None) -> str:
    """
    标准化URL，处理相对URL，去除片段等。
    
    Args:
        url: 原始URL
        base_url: 基础URL，用于解析相对URL
        
    Returns:
        str: 标准化后的URL
    """
    # 处理相对URL
    if base_url and not url.startswith(('http://', 'https://')):
        url = urljoin(base_url, url)
    
    # 解析URL
    parsed = urlparse(url)
    
    # 重构URL，去除片段
    cleaned_url = urlunparse(
        ParseResult(
            scheme=parsed.scheme,
            netloc=parsed.netloc,
            path=parsed.path,
            params=parsed.params,
            query=parsed.query,
            fragment=''  # 去除片段
        )
    )
    
    # 确保URL末尾没有斜杠（除非是根路径）
    if cleaned_url.endswith('/') and len(parsed.path) > 1:
        cleaned_url = cleaned_url[:-1]
    
    return cleaned_url


def is_same_domain(url: str, base_url: str) -> bool:
    """
    检查URL是否与基础URL属于同一域名。
    
    Args:
        url: 要检查的URL
        base_url: 基础URL
        
    Returns:
        bool: 如果属于同一域名则返回True，否则返回False
    """
    # 提取域名
    domain1 = urlparse(url).netloc
    domain2 = urlparse(base_url).netloc
    
    # 如果域名为空，可能是相对URL
    if not domain1 and not url.startswith(('http://', 'https://')):
        return True
    
    return domain1 == domain2


def is_absolute_url(url: str) -> bool:
    """
    检查URL是否是绝对URL。
    
    Args:
        url: 要检查的URL
        
    Returns:
        bool: 如果是绝对URL则返回True，否则返回False
    """
    return bool(urlparse(url).netloc)


def filter_urls(
    urls: List[str],
    base_url: str,
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
    same_domain_only: bool = True
) -> List[str]:
    """
    过滤URL列表。
    
    Args:
        urls: URL列表
        base_url: 基础URL
        include_patterns: 包含模式列表，只有匹配这些模式的URL才会被包含
        exclude_patterns: 排除模式列表，匹配这些模式的URL会被排除
        same_domain_only: 是否只包含同一域名的URL
        
    Returns:
        List[str]: 过滤后的URL列表
    """
    filtered_urls = []
    
    for url in urls:
        # 标准化URL
        normalized_url = normalize_url(url, base_url)
        
        # 检查是否是同一域名
        if same_domain_only and not is_same_domain(normalized_url, base_url):
            continue
        
        # 检查排除模式
        if exclude_patterns:
            excluded = False
            for pattern in exclude_patterns:
                if re.search(pattern, normalized_url):
                    excluded = True
                    break
            if excluded:
                continue
        
        # 检查包含模式
        if include_patterns:
            included = False
            for pattern in include_patterns:
                if re.search(pattern, normalized_url):
                    included = True
                    break
            if not included:
                continue
        
        filtered_urls.append(normalized_url)
    
    return filtered_urls


def extract_domain(url: str) -> str:
    """
    从URL中提取域名。
    
    Args:
        url: URL
        
    Returns:
        str: 域名
    """
    return urlparse(url).netloc


def is_valid_url(url: str) -> bool:
    """
    检查URL是否有效。
    
    Args:
        url: 要检查的URL
        
    Returns:
        bool: 如果URL有效则返回True，否则返回False
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


def urls_to_absolute(urls: List[str], base_url: str) -> List[str]:
    """
    将URL列表转换为绝对URL。
    
    Args:
        urls: URL列表
        base_url: 基础URL
        
    Returns:
        List[str]: 绝对URL列表
    """
    return [normalize_url(url, base_url) for url in urls]


def remove_url_params(url: str) -> str:
    """
    去除URL中的参数。
    
    Args:
        url: 原始URL
        
    Returns:
        str: 去除参数后的URL
    """
    parsed = urlparse(url)
    return urlunparse(
        ParseResult(
            scheme=parsed.scheme,
            netloc=parsed.netloc,
            path=parsed.path,
            params='',
            query='',
            fragment=''
        )
    ) 