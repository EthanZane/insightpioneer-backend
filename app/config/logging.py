"""
日志配置模块，提供日志记录功能。
"""
import sys
import os
from pathlib import Path
from typing import Dict, Any

from loguru import logger

from app.config.settings import get_settings, get_environment


def setup_logging():
    """
    设置日志记录。
    
    配置loguru日志记录器，包括控制台输出和文件输出。
    """
    settings = get_settings()
    
    # 清除默认处理器
    logger.remove()
    
    # 获取日志级别
    log_level = settings.LOG_LEVEL  # 使用配置中的日志级别
    
    # 确保日志目录存在
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 添加控制台处理器（输出到stderr）- 使用更简洁的格式
    logger.add(
        sys.stderr,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {message}",
        level=log_level,
        colorize=True,
        backtrace=True,  # 显示异常回溯
        diagnose=True,   # 显示变量值
    )
    
    # 添加文件处理器（按天轮换）- 使用详细格式记录更多信息
    logger.add(
        log_dir / "insightpioneer_{time:YYYY-MM-DD}.log",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        level=log_level,
        rotation="00:00",  # 每天午夜轮换
        retention="30 days",  # 保留30天
        compression="zip",  # 压缩旧日志
    )
    
    # 添加错误日志处理器
    logger.add(
        log_dir / "error_{time:YYYY-MM-DD}.log",
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation="00:00",
        retention="30 days",
        compression="zip",
    )
    
    # 添加调试日志处理器 - 记录所有日志，包括DEBUG级别
    if os.getenv("ENVIRONMENT", "development") == "development":
        logger.add(
            log_dir / "debug_{time:YYYY-MM-DD}.log",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
            level="DEBUG",
            rotation="00:00",
            retention="7 days",
            compression="zip",
        )
    
    # 为SQLAlchemy设置适当的日志级别 - 减少SQL语句的日志数量
    import logging
    logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.dialects").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.orm").setLevel(logging.WARNING)
    
    return logger


def get_logger(name: str = "insightpioneer"):
    """
    获取命名的日志记录器。
    
    Args:
        name: 日志记录器名称
        
    Returns:
        loguru.logger: 日志记录器
    """
    return logger.bind(name=name)


# 默认导出的日志记录器
default_logger = get_logger()


def masking_sensitive_data(log_record: Dict[str, Any]) -> Dict[str, Any]:
    """
    屏蔽日志记录中的敏感数据。
    
    Args:
        log_record: 日志记录
        
    Returns:
        Dict[str, Any]: 屏蔽敏感数据后的日志记录
    """
    message = log_record["message"]
    
    # 屏蔽数据库连接信息
    if "postgresql://" in message:
        message = message.replace(message[message.find("postgresql://"):message.find("@")+1], "postgresql://****:****@")
    
    # 屏蔽API密钥
    for key_word in ["api_key", "secret", "token", "password"]:
        if key_word in message.lower():
            # 使用正则表达式匹配键值对并替换值部分
            import re
            pattern = f'({key_word}["\']?\\s*[=:]\\s*["\']?)([^"\',\\s]+)(["\',]?)'
            message = re.sub(pattern, r'\1****\3', message, flags=re.IGNORECASE)
    
    log_record["message"] = message
    return log_record


# 安装日志拦截器，用于屏蔽敏感数据
logger = logger.patch(masking_sensitive_data) 