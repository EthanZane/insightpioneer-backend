"""
飞书通知模块，提供向飞书发送通知的功能。
"""
import json
import os
import time
import base64
import hashlib
import hmac
from datetime import datetime
from typing import Dict, Any, List, Optional

import requests
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config.settings import get_settings
from app.models.site import MonitoredSite, DiscoveredPage
from app.utils.time import format_datetime


class FeishuNotifier:
    """
    飞书通知器，用于向飞书发送通知。
    """
    
    def __init__(self, webhook_url: Optional[str] = None, secret: Optional[str] = None):
        """
        初始化飞书通知器。
        
        Args:
            webhook_url: 飞书机器人Webhook URL，如果不提供则从配置或环境变量读取
            secret: 飞书机器人签名密钥，如果不提供则从配置或环境变量读取
        """
        settings = get_settings()
        self.webhook_url = webhook_url or os.getenv("FEISHU_WEBHOOK_URL", settings.FEISHU_WEBHOOK_URL)
        self.secret = secret or os.getenv("FEISHU_SECRET", getattr(settings, "FEISHU_SECRET", ""))
        
        if not self.webhook_url:
            logger.warning("飞书Webhook URL未设置，通知功能将不可用")
        
        if not self.secret:
            logger.warning("飞书签名密钥未设置，通知功能将不可用，请设置FEISHU_SECRET环境变量")
    
    def _generate_sign(self, timestamp: int) -> str:
        """
        生成签名。
        
        Args:
            timestamp: 当前时间戳
            
        Returns:
            str: 生成的签名
        """
        # 按照飞书官方文档的要求组合字符串
        string_to_sign = f"{timestamp}\n{self.secret}"
        # 使用HMAC-SHA256计算签名
        hmac_code = hmac.new(
            string_to_sign.encode("utf-8"),
            digestmod=hashlib.sha256
        ).digest()
        # Base64编码
        sign = base64.b64encode(hmac_code).decode('utf-8')
        return sign
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def send_message(self, msg_type: str, content: Dict[str, Any]) -> bool:
        """
        发送消息到飞书。
        
        Args:
            msg_type: 消息类型，如'text', 'post', 'interactive'等
            content: 消息内容
            
        Returns:
            bool: 发送是否成功
        """
        if not self.webhook_url:
            logger.error("未配置飞书Webhook URL，无法发送通知")
            return False
        
        if not self.secret:
            logger.error("未配置飞书签名密钥，无法发送通知")
            return False
        
        # 准备消息内容
        timestamp = int(time.time())
        sign = self._generate_sign(timestamp)
        
        payload = {
            "timestamp": str(timestamp),
            "sign": sign,
            "msg_type": msg_type,
            "content": content
        }
        
        # 打印详细的请求信息
        logger.debug(f"请求URL: {self.webhook_url}")
        logger.debug(f"请求头: {{'Content-Type': 'application/json'}}")
        logger.debug(f"请求体: {json.dumps(payload, ensure_ascii=False)}")
        
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            # 打印详细的响应信息
            logger.debug(f"响应状态码: {response.status_code}")
            logger.debug(f"响应头: {dict(response.headers)}")
            logger.debug(f"响应体: {response.text}")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("code") == 0:
                    logger.info(f"飞书通知发送成功: {msg_type}")
                    return True
                else:
                    logger.error(f"飞书通知发送失败: {data.get('msg')}")
            else:
                logger.error(f"飞书通知HTTP请求失败，状态码: {response.status_code}")
        
        except Exception as e:
            logger.exception(f"飞书通知发送异常: {str(e)}")
        
        return False
    
    def send_text(self, text: str) -> bool:
        """
        发送文本消息。
        
        Args:
            text: 文本内容
            
        Returns:
            bool: 发送是否成功
        """
        content = {"text": text}
        return self.send_message("text", content)
    
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
        if not new_pages:
            return True  # 没有新页面，不发送通知
        
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 构建文本内容
        text_content = (
            f"⚡ 洞察先锋发现新页面\n\n"
            f"🔍 监控站点: {site.name}\n"
            f"🌐 网站: {site.base_url}\n"
            f"⏰ 发现时间: {now}\n"
            f"📊 新页面数量: {len(new_pages)}\n\n"
            f"📋 新页面列表:\n"
        )
        
        # 添加最多10个新页面
        for i, page in enumerate(new_pages[:10], 1):
            title = f" - {page.page_title}" if page.page_title else ""
            text_content += f"{i}. {page.url}{title}\n"
        
        # 如果有更多页面，添加提示
        if len(new_pages) > 10:
            text_content += f"\n...还有 {len(new_pages) - 10} 个页面未显示"
        
        # 发送通知
        return self.send_text(text_content)
    
    def send_error_notification(self, site: MonitoredSite, error_message: str) -> bool:
        """
        发送错误通知。
        
        Args:
            site: 监控站点
            error_message: 错误消息
            
        Returns:
            bool: 发送是否成功
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        text_content = (
            f"❌ 洞察先锋监控出错\n\n"
            f"🔍 监控站点: {site.name}\n"
            f"🌐 网站: {site.base_url}\n"
            f"⏰ 时间: {now}\n\n"
            f"📝 错误信息:\n{error_message}"
        )
        
        return self.send_text(text_content)
    
    def send_test_notification(self) -> bool:
        """
        发送测试通知。
        
        Returns:
            bool: 发送是否成功
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        text_content = (
            f"🔔 洞察先锋通知测试\n\n"
            f"这是一条测试消息，用于验证飞书通知功能是否正常。\n"
            f"⏰ 发送时间: {now}"
        )
        
        return self.send_text(text_content) 