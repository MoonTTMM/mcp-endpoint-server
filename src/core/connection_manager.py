"""
连接管理器
负责管理WebSocket连接和消息转发
"""

import asyncio
import json
import time
from typing import Dict, Set, Optional, Any
from websockets.server import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosed
from ..utils.logger import get_logger

logger = get_logger()


class ConnectionManager:
    """连接管理器"""

    def __init__(self):
        # 工具端连接: {userId: websocket}
        self.tool_connections: Dict[str, WebSocketServerProtocol] = {}
        # 小智端连接: {userId: websocket}
        self.robot_connections: Dict[str, WebSocketServerProtocol] = {}
        # 连接时间戳: {userId: timestamp}
        self.connection_timestamps: Dict[str, float] = {}
        # 连接锁
        self._lock = asyncio.Lock()

    async def register_tool_connection(
        self, user_id: str, websocket: WebSocketServerProtocol
    ):
        """注册工具端连接"""
        async with self._lock:
            # 如果已存在连接，先关闭旧连接
            if user_id in self.tool_connections:
                old_websocket = self.tool_connections[user_id]
                try:
                    await old_websocket.close(1000, "新连接替换")
                except Exception as e:
                    logger.warning(f"关闭旧工具端连接失败: {e}")

            self.tool_connections[user_id] = websocket
            self.connection_timestamps[user_id] = time.time()
            logger.info(f"工具端连接已注册: {user_id}")

    async def register_robot_connection(
        self, user_id: str, websocket: WebSocketServerProtocol
    ):
        """注册小智端连接"""
        async with self._lock:
            # 如果已存在连接，先关闭旧连接
            if user_id in self.robot_connections:
                old_websocket = self.robot_connections[user_id]
                try:
                    await old_websocket.close(1000, "新连接替换")
                except Exception as e:
                    logger.warning(f"关闭旧机器人连接失败: {e}")

            self.robot_connections[user_id] = websocket
            self.connection_timestamps[user_id] = time.time()
            logger.info(f"小智端连接已注册: {user_id}")

    async def unregister_tool_connection(self, user_id: str):
        """注销工具端连接"""
        async with self._lock:
            if user_id in self.tool_connections:
                del self.tool_connections[user_id]
                if user_id in self.connection_timestamps:
                    del self.connection_timestamps[user_id]
                logger.info(f"工具端连接已注销: {user_id}")

    async def unregister_robot_connection(self, user_id: str):
        """注销小智端连接"""
        async with self._lock:
            if user_id in self.robot_connections:
                del self.robot_connections[user_id]
                if user_id in self.connection_timestamps:
                    del self.connection_timestamps[user_id]
                logger.info(f"小智端连接已注销: {user_id}")

    async def forward_to_tool(self, user_id: str, message: Any) -> bool:
        """转发消息给工具端"""
        async with self._lock:
            if user_id not in self.tool_connections:
                logger.warning(f"工具端连接不存在: {user_id}")
                return False

            websocket = self.tool_connections[user_id]
            try:
                await websocket.send_text(message)
                logger.debug(f"消息已转发给工具端 {user_id}: {message[:100]}...")
                return True
            except ConnectionClosed:
                logger.warning(f"工具端连接已关闭: {user_id}")
                await self.unregister_tool_connection(user_id)
                return False
            except Exception as e:
                logger.error(f"转发消息给工具端失败: {e}")
                return False

    async def forward_to_robot(self, user_id: str, message: Any) -> bool:
        """转发消息给小智端"""
        async with self._lock:
            if user_id not in self.robot_connections:
                logger.warning(f"小智端连接不存在: {user_id}")
                return False

            websocket = self.robot_connections[user_id]
            try:
                await websocket.send_text(message)
                logger.debug(f"消息已转发给小智端 {user_id}: {message[:100]}...")
                return True
            except ConnectionClosed:
                logger.warning(f"小智端连接已关闭: {user_id}")
                await self.unregister_robot_connection(user_id)
                return False
            except Exception as e:
                logger.error(f"转发消息给小智端失败: {e}")
                return False

    def get_connection_stats(self) -> Dict[str, Any]:
        """获取连接统计信息"""
        return {
            "tool_connections": len(self.tool_connections),
            "robot_connections": len(self.robot_connections),
            "total_connections": len(self.tool_connections)
            + len(self.robot_connections),
            "tool_user_ids": list(self.tool_connections.keys()),
            "robot_user_ids": list(self.robot_connections.keys()),
        }

    def is_tool_connected(self, user_id: str) -> bool:
        """检查工具端是否已连接"""
        return user_id in self.tool_connections

    def is_robot_connected(self, user_id: str) -> bool:
        """检查小智端是否已连接"""
        return user_id in self.robot_connections

    async def cleanup_inactive_connections(self, timeout_seconds: int = 300):
        """清理不活跃的连接"""
        current_time = time.time()
        async with self._lock:
            inactive_users = []
            for user_id, timestamp in self.connection_timestamps.items():
                if current_time - timestamp > timeout_seconds:
                    inactive_users.append(user_id)

            for user_id in inactive_users:
                logger.info(f"清理不活跃连接: {user_id}")
                await self.unregister_tool_connection(user_id)
                await self.unregister_robot_connection(user_id)


# 全局连接管理器实例
connection_manager = ConnectionManager()
