"""
通知器基类模块，提供通知功能的基础接口。
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

from app.models.site import MonitoredSite, DiscoveredPage


class BaseNotifier(ABC):
    """
    通知器基类，定义通知功能的通用接口。
    """
    
    @abstractmethod
    def send_message(self, msg_type: str, content: Dict[str, Any]) -> bool:
        """
        发送消息。
        
        Args:
            msg_type: 消息类型
            content: 消息内容
            
        Returns:
            bool: 发送是否成功
        """
        pass
    
    @abstractmethod
    def send_new_pages_notification(
        self, site: MonitoredSite, new_pages: List[DiscoveredPage]
    ) -> bool:
        """
        发送新页面通知。
        
        Args:
            site: 监控站点
            new_pages: 新发现的页面列表
            
        Returns:
            bool: 发送是否成功
        """
        pass
    
    @abstractmethod
    def send_error_notification(self, site: MonitoredSite, error_message: str) -> bool:
        """
        发送错误通知。
        
        Args:
            site: 监控站点
            error_message: 错误消息
            
        Returns:
            bool: 发送是否成功
        """
        pass
    
    @abstractmethod
    def send_test_notification(self) -> bool:
        """
        发送测试通知。
        
        Returns:
            bool: 发送是否成功
        """
        pass 