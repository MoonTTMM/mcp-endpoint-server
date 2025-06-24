"""
连接管理器
负责管理WebSocket连接和消息转发
"""

import asyncio
import json
import time
from typing import Dict, Any
from websockets.server import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosed
from ..utils.logger import get_logger

logger = get_logger()


class ConnectionManager:
    """连接管理器"""

    def __init__(self):
        # 工具端连接: {agentId: websocket}
        self.tool_connections: Dict[str, WebSocketServerProtocol] = {}
        # 小智端连接: {agentId: websocket}
        self.robot_connections: Dict[str, WebSocketServerProtocol] = {}
        # 连接时间戳: {agentId: timestamp}
        self.connection_timestamps: Dict[str, float] = {}
        # 连接锁
        self._lock = asyncio.Lock()

    async def register_tool_connection(
        self, agent_id: str, websocket: WebSocketServerProtocol
    ):
        """注册工具端连接"""
        async with self._lock:
            # 如果已存在连接，先关闭旧连接
            if agent_id in self.tool_connections:
                old_websocket = self.tool_connections[agent_id]
                try:
                    await old_websocket.close(1000, "新连接替换")
                except Exception as e:
                    logger.warning(f"关闭旧工具端连接失败: {e}")

            self.tool_connections[agent_id] = websocket
            self.connection_timestamps[agent_id] = time.time()
            logger.info(f"工具端连接已注册: {agent_id}")

    async def register_robot_connection(
        self, agent_id: str, websocket: WebSocketServerProtocol
    ):
        """注册小智端连接"""
        async with self._lock:
            # 如果已存在连接，先关闭旧连接
            if agent_id in self.robot_connections:
                old_websocket = self.robot_connections[agent_id]
                try:
                    await old_websocket.close(1000, "新连接替换")
                except Exception as e:
                    logger.warning(f"关闭旧机器人连接失败: {e}")

            self.robot_connections[agent_id] = websocket
            self.connection_timestamps[agent_id] = time.time()
            logger.info(f"小智端连接已注册: {agent_id}")

    async def unregister_tool_connection(self, agent_id: str):
        """注销工具端连接"""
        async with self._lock:
            if agent_id in self.tool_connections:
                del self.tool_connections[agent_id]
                if agent_id in self.connection_timestamps:
                    del self.connection_timestamps[agent_id]
                logger.info(f"工具端连接已注销: {agent_id}")

    async def unregister_robot_connection(self, agent_id: str):
        """注销小智端连接"""
        async with self._lock:
            if agent_id in self.robot_connections:
                del self.robot_connections[agent_id]
                if agent_id in self.connection_timestamps:
                    del self.connection_timestamps[agent_id]
                logger.info(f"小智端连接已注销: {agent_id}")

    async def forward_to_tool(self, agent_id: str, message: Any) -> bool:
        """转发消息给工具端"""
        async with self._lock:
            if agent_id not in self.tool_connections:
                logger.warning(f"工具端连接不存在: {agent_id}")
                return False

            websocket = self.tool_connections[agent_id]
            try:
                # 确保消息是字符串格式
                if isinstance(message, dict):
                    message_str = json.dumps(message, ensure_ascii=False)
                elif isinstance(message, str):
                    message_str = message
                else:
                    message_str = str(message)

                await websocket.send_text(message_str)
                logger.debug(f"消息已转发给工具端 {agent_id}: {message_str[:100]}...")
                return True
            except ConnectionClosed:
                logger.warning(f"工具端连接已关闭: {agent_id}")
                await self.unregister_tool_connection(agent_id)
                return False
            except Exception as e:
                logger.error(f"转发消息给工具端失败: {e}")
                return False

    async def forward_to_robot(self, agent_id: str, message: Any) -> bool:
        """转发消息给小智端"""
        async with self._lock:
            if agent_id not in self.robot_connections:
                logger.warning(f"小智端连接不存在: {agent_id}")
                return False

            websocket = self.robot_connections[agent_id]
            try:
                # 确保消息是字符串格式
                if isinstance(message, dict):
                    message_str = json.dumps(message, ensure_ascii=False)
                elif isinstance(message, str):
                    message_str = message
                else:
                    message_str = str(message)

                await websocket.send_text(message_str)
                logger.debug(f"消息已转发给小智端 {agent_id}: {message_str[:100]}...")
                return True
            except ConnectionClosed:
                logger.warning(f"小智端连接已关闭: {agent_id}")
                await self.unregister_robot_connection(agent_id)
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
        }

    def is_tool_connected(self, agent_id: str) -> bool:
        """检查工具端是否已连接"""
        return agent_id in self.tool_connections

    def is_robot_connected(self, agent_id: str) -> bool:
        """检查小智端是否已连接"""
        return agent_id in self.robot_connections

    async def cleanup_inactive_connections(self, timeout_seconds: int = 300):
        """清理不活跃的连接"""
        current_time = time.time()
        async with self._lock:
            inactive_users = []
            for agent_id, timestamp in self.connection_timestamps.items():
                if current_time - timestamp > timeout_seconds:
                    inactive_users.append(agent_id)

            for agent_id in inactive_users:
                logger.info(f"清理不活跃连接: {agent_id}")
                await self.unregister_tool_connection(agent_id)
                await self.unregister_robot_connection(agent_id)


# 全局连接管理器实例
connection_manager = ConnectionManager()
