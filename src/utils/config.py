"""
配置管理工具
"""

import os
import configparser
from typing import Optional
from pathlib import Path


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_file: str = "data/.mcp-endpoint-server.cfg"):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self._load_config()

    def _load_config(self):
        """加载配置文件"""
        if os.path.exists(self.config_file):
            self.config.read(self.config_file, encoding="utf-8")
        else:
            # 如果配置文件不存在，使用默认配置
            self._create_default_config()

    def _create_default_config(self):
        """创建默认配置"""
        self.config["server"] = {
            "host": "127.0.0.1",
            "port": "8004",
            "debug": "false",
            "log_level": "INFO",
        }

        self.config["websocket"] = {
            "max_connections": "1000",
            "ping_interval": "30",
            "ping_timeout": "10",
            "close_timeout": "10",
        }

        self.config["security"] = {"allowed_origins": "*", "enable_cors": "true"}

        self.config["logging"] = {
            "log_file": "logs/mcp_server.log",
            "max_file_size": "10MB",
            "backup_count": "5",
        }

        # 确保目录存在
        os.makedirs(os.path.dirname(self.config_file), exist_ok=True)

        # 保存默认配置
        with open(self.config_file, "w", encoding="utf-8") as f:
            self.config.write(f)

    def get(self, section: str, key: str, default: Optional[str] = None) -> str:
        """获取配置值"""
        try:
            return self.config.get(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return default

    def getint(self, section: str, key: str, default: int = 0) -> int:
        """获取整数配置值"""
        try:
            return self.config.getint(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return default

    def getboolean(self, section: str, key: str, default: bool = False) -> bool:
        """获取布尔配置值"""
        try:
            return self.config.getboolean(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return default

    def reload(self):
        """重新加载配置"""
        self._load_config()


# 全局配置实例
config = ConfigManager()
