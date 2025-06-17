"""
HTTP请求工具模块，提供HTTP请求相关功能。
"""
import random
import time
from typing import Dict, Any, Optional, Tuple, Union

import requests
from loguru import logger
from requests import Response
from requests.exceptions import RequestException
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.config.settings import get_settings


def get_random_user_agent() -> str:
    """
    从配置的User-Agent列表中随机获取一个User-Agent。
    
    Returns:
        str: 随机User-Agent
    """
    settings = get_settings()
    return random.choice(settings.USER_AGENT_LIST)


def create_session(
    user_agent: Optional[str] = None,
    proxy: Optional[str] = None,
    timeout: Optional[int] = None,
    verify: bool = True
) -> requests.Session:
    """
    创建一个配置好的requests会话。
    
    Args:
        user_agent: 用户代理字符串
        proxy: 代理服务器URL
        timeout: 请求超时时间
        verify: 是否验证SSL证书
        
    Returns:
        requests.Session: 配置好的会话
    """
    settings = get_settings()
    
    session = requests.Session()
    
    # 设置User-Agent
    if user_agent:
        session.headers.update({"User-Agent": user_agent})
    else:
        session.headers.update({"User-Agent": get_random_user_agent()})
    
    # 设置代理
    if proxy:
        session.proxies = {"http": proxy, "https": proxy}
    
    # 设置超时
    session.timeout = timeout or settings.HTTP_TIMEOUT
    
    # 设置SSL验证
    session.verify = verify
    
    return session


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((RequestException, ConnectionError, TimeoutError))
)
def make_request(
    url: str,
    method: str = "GET",
    params: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    user_agent: Optional[str] = None,
    proxy: Optional[str] = None,
    timeout: Optional[int] = None,
    verify: bool = True,
    allow_redirects: bool = True,
    delay: Optional[float] = None
) -> Response:
    """
    发送HTTP请求，带有重试功能。
    
    Args:
        url: 请求URL
        method: 请求方法，如"GET"、"POST"等
        params: URL参数
        data: 请求体数据
        headers: 请求头
        user_agent: 用户代理字符串
        proxy: 代理服务器URL
        timeout: 请求超时时间
        verify: 是否验证SSL证书
        allow_redirects: 是否允许重定向
        delay: 请求前等待的时间（秒）
        
    Returns:
        Response: 请求响应
        
    Raises:
        RequestException: 请求失败
    """
    settings = get_settings()
    
    # 应用爬取延迟（如果配置）
    if delay is not None:
        time.sleep(delay)
    elif settings.DEFAULT_CRAWL_DELAY > 0:
        time.sleep(settings.DEFAULT_CRAWL_DELAY)
    
    # 准备请求头
    _headers = {}
    if headers:
        _headers.update(headers)
    
    # 添加User-Agent
    if user_agent:
        _headers["User-Agent"] = user_agent
    elif "User-Agent" not in _headers:
        _headers["User-Agent"] = get_random_user_agent()
    
    # 准备代理
    proxies = None
    if proxy:
        proxies = {"http": proxy, "https": proxy}
    
    # 设置超时
    _timeout = timeout or settings.HTTP_TIMEOUT
    
    try:
        response = requests.request(
            method=method,
            url=url,
            params=params,
            data=data,
            headers=_headers,
            proxies=proxies,
            timeout=_timeout,
            verify=verify,
            allow_redirects=allow_redirects
        )
        
        # 记录请求信息
        log_level = "INFO" if response.status_code < 400 else "ERROR"
        getattr(logger, log_level.lower())(
            f"HTTP {method} {url} - 状态码: {response.status_code}"
        )
        
        # 检查状态码
        response.raise_for_status()
        
        return response
        
    except RequestException as e:
        logger.error(f"请求失败: {url} - {str(e)}")
        raise e


def download_file(
    url: str,
    output_path: str,
    user_agent: Optional[str] = None,
    proxy: Optional[str] = None,
    timeout: Optional[int] = None,
    chunk_size: int = 8192
) -> bool:
    """
    下载文件。
    
    Args:
        url: 文件URL
        output_path: 输出文件路径
        user_agent: 用户代理字符串
        proxy: 代理服务器URL
        timeout: 请求超时时间
        chunk_size: 数据块大小
        
    Returns:
        bool: 下载是否成功
    """
    try:
        response = make_request(
            url=url,
            user_agent=user_agent,
            proxy=proxy,
            timeout=timeout,
            allow_redirects=True,
            stream=True
        )
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
        
        return True
        
    except Exception as e:
        logger.error(f"文件下载失败: {url} - {str(e)}")
        return False


def check_url_status(url: str, **kwargs) -> Tuple[bool, int]:
    """
    检查URL状态。
    
    Args:
        url: 要检查的URL
        **kwargs: 传递给make_request的其他参数
        
    Returns:
        Tuple[bool, int]: (URL是否可访问, 状态码)
    """
    try:
        response = make_request(url=url, method="HEAD", **kwargs)
        return True, response.status_code
    except RequestException:
        return False, 0 