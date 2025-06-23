"""
日志管理工具
"""

import logging
import logging.handlers
import os
from typing import Optional
from .config import config


class LoggerManager:
    """日志管理器"""

    def __init__(self):
        self.logger = None
        self._setup_logger()

    def _setup_logger(self):
        """设置日志器"""
        self.logger = logging.getLogger("mcp_server")

        # 设置日志级别
        log_level = config.get("server", "log_level", "INFO")
        self.logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

        # 清除现有的处理器
        self.logger.handlers.clear()

        # 创建格式化器
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # 文件处理器
        log_file = config.get("logging", "log_file", "logs/mcp_server.log")
        if log_file:
            # 确保日志目录存在
            os.makedirs(os.path.dirname(log_file), exist_ok=True)

            # 获取文件大小限制
            max_file_size = config.get("logging", "max_file_size", "10MB")
            max_bytes = self._parse_size(max_file_size)

            # 获取备份数量
            backup_count = config.getint("logging", "backup_count", 5)

            # 创建轮转文件处理器
            file_handler = logging.handlers.RotatingFileHandler(
                log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
            )
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)

    def _parse_size(self, size_str: str) -> int:
        """解析文件大小字符串"""
        size_str = size_str.upper()
        if size_str.endswith("MB"):
            return int(float(size_str[:-2]) * 1024 * 1024)
        elif size_str.endswith("KB"):
            return int(float(size_str[:-2]) * 1024)
        elif size_str.endswith("B"):
            return int(size_str[:-1])
        else:
            return int(size_str)

    def get_logger(self) -> logging.Logger:
        """获取日志器"""
        return self.logger

    def reload(self):
        """重新加载日志配置"""
        self._setup_logger()


# 全局日志管理器实例
logger_manager = LoggerManager()


def get_logger() -> logging.Logger:
    """获取日志器"""
    return logger_manager.get_logger()
