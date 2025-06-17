#!/usr/bin/env python
"""
报告执行失败的脚本。
"""
import os
import sys
from datetime import datetime

# 将项目根目录添加到Python路径
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
sys.path.insert(0, project_root)

from app.config.logging import setup_logging
from app.notifiers.feishu import FeishuNotifier


def main() -> int:
    """
    主函数。
    
    Returns:
        int: 退出码，0表示成功，非0表示失败
    """
    # 设置日志
    setup_logging()
    
    # 获取GitHub Actions相关信息
    run_id = os.environ.get("GITHUB_RUN_ID", "未知")
    workflow = os.environ.get("GITHUB_WORKFLOW", "未知")
    repository = os.environ.get("GITHUB_REPOSITORY", "未知")
    server_url = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    
    # 组装运行URL
    run_url = f"{server_url}/{repository}/actions/runs/{run_id}"
    
    # 组装通知消息
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = (
        f"❌ 执行失败\n\n"
        f"📊 工作流: {workflow}\n"
        f"🏢 仓库: {repository}\n"
        f"🔄 运行ID: {run_id}\n"
        f"⏰ 时间: {now}\n\n"
        f"🔍 详情: {run_url}"
    )
    
    # 发送通知
    notifier = FeishuNotifier()
    success = notifier.send_text(message)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main()) 