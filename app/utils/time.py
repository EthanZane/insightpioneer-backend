"""
时间处理工具模块，提供时间日期相关功能。
"""
import time
from datetime import datetime, timedelta, timezone
from typing import Optional, Union


def utc_now() -> datetime:
    """
    获取当前UTC时间。
    
    Returns:
        datetime: 当前UTC时间
    """
    return datetime.now(timezone.utc)


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    格式化日期时间。
    
    Args:
        dt: 日期时间对象
        format_str: 格式字符串
        
    Returns:
        str: 格式化后的日期时间字符串
    """
    return dt.strftime(format_str)


def parse_datetime(date_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> Optional[datetime]:
    """
    解析日期时间字符串。
    
    Args:
        date_str: 日期时间字符串
        format_str: 格式字符串
        
    Returns:
        Optional[datetime]: 解析后的日期时间对象，解析失败则返回None
    """
    try:
        return datetime.strptime(date_str, format_str)
    except (ValueError, TypeError):
        return None


def parse_iso_datetime(date_str: str) -> Optional[datetime]:
    """
    解析ISO格式的日期时间字符串。
    
    Args:
        date_str: ISO格式的日期时间字符串
        
    Returns:
        Optional[datetime]: 解析后的日期时间对象，解析失败则返回None
    """
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except (ValueError, TypeError, AttributeError):
        return None


def time_elapsed(dt: datetime) -> str:
    """
    计算从指定时间到现在经过的时间，并返回可读的字符串表示。
    
    Args:
        dt: 起始时间
        
    Returns:
        str: 可读的时间差字符串
    """
    now = utc_now()
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    delta = now - dt
    seconds = delta.total_seconds()
    
    if seconds < 60:
        return f"{int(seconds)}秒前"
    elif seconds < 3600:
        return f"{int(seconds // 60)}分钟前"
    elif seconds < 86400:
        return f"{int(seconds // 3600)}小时前"
    elif seconds < 2592000:
        return f"{int(seconds // 86400)}天前"
    elif seconds < 31536000:
        return f"{int(seconds // 2592000)}个月前"
    else:
        return f"{int(seconds // 31536000)}年前"


def add_time(
    dt: datetime,
    days: int = 0,
    hours: int = 0,
    minutes: int = 0,
    seconds: int = 0
) -> datetime:
    """
    在指定时间上添加时间。
    
    Args:
        dt: 原始时间
        days: 添加的天数
        hours: 添加的小时数
        minutes: 添加的分钟数
        seconds: 添加的秒数
        
    Returns:
        datetime: 增加时间后的日期时间对象
    """
    return dt + timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)


def subtract_time(
    dt: datetime,
    days: int = 0,
    hours: int = 0,
    minutes: int = 0,
    seconds: int = 0
) -> datetime:
    """
    从指定时间上减去时间。
    
    Args:
        dt: 原始时间
        days: 减去的天数
        hours: 减去的小时数
        minutes: 减去的分钟数
        seconds: 减去的秒数
        
    Returns:
        datetime: 减去时间后的日期时间对象
    """
    return dt - timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)


def datetime_to_timestamp(dt: datetime) -> int:
    """
    将日期时间对象转换为时间戳（秒）。
    
    Args:
        dt: 日期时间对象
        
    Returns:
        int: 时间戳（秒）
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp())


def timestamp_to_datetime(timestamp: Union[int, float]) -> datetime:
    """
    将时间戳（秒）转换为日期时间对象。
    
    Args:
        timestamp: 时间戳（秒）
        
    Returns:
        datetime: 日期时间对象
    """
    return datetime.fromtimestamp(timestamp, tz=timezone.utc)


def measure_execution_time(func):
    """
    测量函数执行时间的装饰器。
    
    Args:
        func: 要测量的函数
        
    Returns:
        callable: 包装后的函数
    """
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"函数 {func.__name__} 执行时间: {end_time - start_time:.4f} 秒")
        return result
    return wrapper 