"""
WebSocket处理器
处理工具端和小智端的WebSocket连接
"""

import json
import asyncio
from typing import Optional, Any
from urllib.parse import parse_qs, urlparse
from websockets.server import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosed
from ..core.connection_manager import connection_manager
from ..utils.logger import get_logger

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
            # 解析URL参数获取userId
            user_id = self._extract_user_id(path)
            if not user_id:
                await websocket.close(1008, "缺少userId参数")
                return

            # 注册连接
            await connection_manager.register_tool_connection(user_id, websocket)

            # 发送连接确认消息
            await websocket.send(
                json.dumps(
                    {
                        "type": "connection_established",
                        "message": "工具端连接已建立",
                        "user_id": user_id,
                    },
                    ensure_ascii=False,
                )
            )

            logger.info(f"工具端连接已建立: {user_id}")

            # 处理消息
            async for message in websocket:
                await self._handle_tool_message(user_id, message)

        except ConnectionClosed:
            logger.info(
                f"工具端连接已关闭: {user_id if 'user_id' in locals() else 'unknown'}"
            )
        except Exception as e:
            logger.error(f"处理工具端连接时发生错误: {e}")
        finally:
            if "user_id" in locals():
                await connection_manager.unregister_tool_connection(user_id)

    async def handle_robot_connection(
        self, websocket: WebSocketServerProtocol, path: str
    ):
        """处理小智端连接"""
        try:
            # 解析URL参数获取userId
            user_id = self._extract_user_id(path)
            if not user_id:
                await websocket.close(1008, "缺少userId参数")
                return

            # 注册连接
            await connection_manager.register_robot_connection(user_id, websocket)

            # 发送连接确认消息
            await websocket.send(
                json.dumps(
                    {
                        "type": "connection_established",
                        "message": "小智端连接已建立",
                        "user_id": user_id,
                    },
                    ensure_ascii=False,
                )
            )

            logger.info(f"小智端连接已建立: {user_id}")

            # 处理消息
            async for message in websocket:
                await self._handle_robot_message(user_id, message)

        except ConnectionClosed:
            logger.info(
                f"小智端连接已关闭: {user_id if 'user_id' in locals() else 'unknown'}"
            )
        except Exception as e:
            logger.error(f"处理小智端连接时发生错误: {e}")
        finally:
            if "user_id" in locals():
                await connection_manager.unregister_robot_connection(user_id)

    async def _handle_tool_message(self, user_id: str, message: str):
        """处理工具端消息"""
        try:
            # 解析消息
            logger.debug(f"收到工具端消息: {user_id} - {message}")

            # 检查是否有对应的小智端连接
            if not connection_manager.is_robot_connected(user_id):
                logger.warning(f"小智端未连接: {user_id}")
                return

            # 转发消息给小智端
            success = await connection_manager.forward_to_robot(user_id, message)
            if not success:
                logger.error(f"转发消息给小智端失败: {user_id}")

        except json.JSONDecodeError:
            logger.error(f"工具端消息格式错误: {message}")
        except Exception as e:
            logger.error(f"处理工具端消息时发生错误: {e}")

    async def _handle_robot_message(self, user_id: str, message: str):
        """处理小智端消息"""
        try:
            # 解析消息
            logger.debug(f"收到小智端消息: {user_id} - {message}")

            # 检查是否有对应的工具端连接
            if not connection_manager.is_tool_connected(user_id):
                logger.warning(f"工具端未连接: {user_id}")
                # 发送错误消息给小智端
                error_response = {
                    "type": "error",
                    "message": "工具端未连接",
                    "user_id": user_id,
                }
                await connection_manager.forward_to_robot(user_id, error_response)
                return

            # 转发消息给工具端
            success = await connection_manager.forward_to_tool(user_id, message)
            if not success:
                logger.error(f"转发消息给工具端失败: {user_id}")
                # 发送错误消息给小智端
                error_response = {
                    "type": "error",
                    "message": "转发消息给工具端失败",
                    "user_id": user_id,
                }
                await connection_manager.forward_to_robot(user_id, error_response)

        except json.JSONDecodeError:
            logger.error(f"小智端消息格式错误: {message}")
        except Exception as e:
            logger.error(f"处理小智端消息时发生错误: {e}")

    def _extract_user_id(self, path: str) -> Optional[str]:
        """从路径中提取userId参数"""
        try:
            parsed_url = urlparse(f"ws://localhost{path}")
            query_params = parse_qs(parsed_url.query)
            user_ids = query_params.get("userId", [])
            return user_ids[0] if user_ids else None
        except Exception as e:
            logger.error(f"提取userId参数失败: {e}")
            return None


# 全局WebSocket处理器实例
websocket_handler = WebSocketHandler()
