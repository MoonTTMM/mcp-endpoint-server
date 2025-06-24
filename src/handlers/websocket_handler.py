"""
WebSocket处理器
处理工具端和小智端的WebSocket连接
"""

import json
from typing import Optional, Any
from urllib.parse import parse_qs, urlparse
from websockets.server import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosed
from ..core.connection_manager import connection_manager
from ..utils.logger import get_logger
from ..utils.jsonrpc import (
    JSONRPCProtocol,
    create_connection_established_message,
    create_tool_not_connected_error,
    create_forward_failed_error,
)

logger = get_logger()


class WebSocketHandler:
    """WebSocket处理器"""

    def __init__(self):
        pass

    async def handle_tool_connection(
        self, websocket: WebSocketServerProtocol, path: str
    ):
        """处理工具端连接"""
        try:
            # 解析URL参数获取agentId
            agent_id = self._extract_agent_id(path)
            if not agent_id:
                await websocket.close(1008, "缺少agentId参数")
                return

            # 注册连接
            await connection_manager.register_tool_connection(agent_id, websocket)

            # 发送连接确认消息
            connection_message = create_connection_established_message(
                agent_id, "工具端连接已建立"
            )
            await websocket.send(connection_message)

            logger.info(f"工具端连接已建立: {agent_id}")

            # 处理消息
            async for message in websocket:
                await self._handle_tool_message(agent_id, message)

        except ConnectionClosed:
            logger.info(
                f"工具端连接已关闭: {agent_id if 'agent_id' in locals() else 'unknown'}"
            )
        except Exception as e:
            logger.error(f"处理工具端连接时发生错误: {e}")
        finally:
            if "agent_id" in locals():
                await connection_manager.unregister_tool_connection(agent_id)

    async def handle_robot_connection(
        self, websocket: WebSocketServerProtocol, path: str
    ):
        """处理小智端连接"""
        try:
            # 解析URL参数获取agentId
            agent_id = self._extract_agent_id(path)
            if not agent_id:
                await websocket.close(1008, "缺少agentId参数")
                return

            # 注册连接
            await connection_manager.register_robot_connection(agent_id, websocket)

            # 发送连接确认消息
            connection_message = create_connection_established_message(
                agent_id, "小智端连接已建立"
            )
            await websocket.send(connection_message)

            logger.info(f"小智端连接已建立: {agent_id}")

            # 处理消息
            async for message in websocket:
                await self._handle_robot_message(agent_id, message)

        except ConnectionClosed:
            logger.info(
                f"小智端连接已关闭: {agent_id if 'agent_id' in locals() else 'unknown'}"
            )
        except Exception as e:
            logger.error(f"处理小智端连接时发生错误: {e}")
        finally:
            if "agent_id" in locals():
                await connection_manager.unregister_robot_connection(agent_id)

    async def _handle_tool_message(self, agent_id: str, message: str):
        """处理工具端消息"""
        try:
            # 解析消息
            logger.debug(f"收到工具端消息: {agent_id} - {message}")

            # 检查是否有对应的小智端连接
            if not connection_manager.is_robot_connected(agent_id):
                logger.warning(f"小智端未连接: {agent_id}")
                return

            # 转发消息给小智端
            success = await connection_manager.forward_to_robot(agent_id, message)
            if not success:
                logger.error(f"转发消息给小智端失败: {agent_id}")

        except json.JSONDecodeError:
            logger.error(f"工具端消息格式错误: {message}")
        except Exception as e:
            logger.error(f"处理工具端消息时发生错误: {e}")

    async def _handle_robot_message(self, agent_id: str, message: str):
        """处理小智端消息"""
        try:
            # 解析消息
            logger.debug(f"收到小智端消息: {agent_id} - {message}")

            # 尝试解析JSON-RPC消息以获取id
            request_id = None
            try:
                message_data = json.loads(message)
                request_id = message_data.get("id")
            except json.JSONDecodeError:
                logger.warning(f"小智端消息不是有效的JSON格式: {message}")
                # 如果消息不是JSON格式，仍然检查工具端连接状态

            # 检查是否有对应的工具端连接
            if not connection_manager.is_tool_connected(agent_id):
                logger.warning(f"工具端未连接: {agent_id}")
                # 发送JSON-RPC格式的错误消息给小智端
                error_message = create_tool_not_connected_error(request_id, agent_id)
                await connection_manager.forward_to_robot(agent_id, error_message)
                return

            # 转发消息给工具端
            success = await connection_manager.forward_to_tool(agent_id, message)
            if not success:
                logger.error(f"转发消息给工具端失败: {agent_id}")
                # 发送JSON-RPC格式的错误消息给小智端
                error_message = create_forward_failed_error(request_id, agent_id)
                await connection_manager.forward_to_robot(agent_id, error_message)

        except json.JSONDecodeError:
            logger.error(f"小智端消息格式错误: {message}")
        except Exception as e:
            logger.error(f"处理小智端消息时发生错误: {e}")

    def _extract_agent_id(self, path: str) -> Optional[str]:
        """从路径中提取agentId参数"""
        try:
            parsed_url = urlparse(f"ws://localhost{path}")
            query_params = parse_qs(parsed_url.query)
            agent_ids = query_params.get("agentId", [])
            return agent_ids[0] if agent_ids else None
        except Exception as e:
            logger.error(f"提取agentId参数失败: {e}")
            return None


# 全局WebSocket处理器实例
websocket_handler = WebSocketHandler()
