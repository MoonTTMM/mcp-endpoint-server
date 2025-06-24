"""
MCP Endpoint Server
主服务器文件
"""

import asyncio
import signal
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
import uvicorn
from websockets.server import serve

from .core.connection_manager import connection_manager
from .handlers.websocket_handler import websocket_handler
from .utils.config import config
from .utils.logger import get_logger

logger = get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("MCP Endpoint Server 正在启动...")
    logger.info(f"======================================================")
    logger.info(
        f"接口地址: http://{config.get('server', 'host', '127.0.0.1')}:{config.getint('server', 'port', 8004)}/mcp_endpoint/health?key={config.get('server', 'key', '')}"
    )
    logger.info("=======上面的地址是websocket协议地址，请勿用浏览器访问=======")
    yield
    # 关闭时
    logger.info("MCP Endpoint Server 已关闭")


# 创建FastAPI应用
app = FastAPI(
    title="MCP Endpoint Server",
    description="高效的WebSocket中转服务器",
    version="1.0.0",
    lifespan=lifespan,
)

# 配置CORS
if config.getboolean("security", "enable_cors", True):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[config.get("security", "allowed_origins", "*")],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/")
async def redirect_root():
    """根路径重定向到 /mcp_endpoint/"""
    return RedirectResponse(url="/mcp_endpoint/")


@app.get("/mcp_endpoint/")
async def root():
    """根路径"""
    return {"message": "MCP Endpoint Server", "version": "1.0.0", "status": "running"}


@app.get("/mcp_endpoint/health")
async def health_check(key: str = None):
    """健康检查"""
    # 验证key参数
    expected_key = config.get("server", "key", "")
    if not key or key != expected_key:
        return {"status": "key_error"}

    stats = connection_manager.get_connection_stats()
    return {"status": "success", "connections": stats}


@app.websocket("/mcp_endpoint/mcp/")
async def websocket_tool_endpoint(websocket: WebSocket):
    """工具端WebSocket端点"""
    await websocket.accept()

    # 获取userId参数
    user_id = websocket.query_params.get("userId")
    if not user_id:
        await websocket.close(code=1008, reason="缺少userId参数")
        return

    try:
        # 注册连接
        await connection_manager.register_tool_connection(user_id, websocket)

        # 发送连接确认消息
        await websocket.send_text(
            '{"type": "connection_established", "message": "工具端连接已建立", "user_id": "'
            + user_id
            + '"}'
        )

        logger.info(f"工具端连接已建立: {user_id}")

        # 处理消息
        while True:
            try:
                message = await websocket.receive_text()
                await websocket_handler._handle_tool_message(user_id, message)
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"处理工具端消息时发生错误: {e}")
                break

    except Exception as e:
        logger.error(f"处理工具端连接时发生错误: {e}")
    finally:
        await connection_manager.unregister_tool_connection(user_id)
        logger.info(f"工具端连接已关闭: {user_id}")


@app.websocket("/mcp_endpoint/call/")
async def websocket_robot_endpoint(websocket: WebSocket):
    """小智端WebSocket端点"""
    await websocket.accept()

    # 获取userId参数
    user_id = websocket.query_params.get("userId")
    if not user_id:
        await websocket.close(code=1008, reason="缺少userId参数")
        return

    try:
        # 注册连接
        await connection_manager.register_robot_connection(user_id, websocket)

        # 发送连接确认消息
        await websocket.send_text(
            '{"type": "connection_established", "message": "小智端连接已建立", "user_id": "'
            + user_id
            + '"}'
        )

        logger.info(f"小智端连接已建立: {user_id}")

        # 处理消息
        while True:
            try:
                message = await websocket.receive_text()
                await websocket_handler._handle_robot_message(user_id, message)
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"处理小智端消息时发生错误: {e}")
                break

    except Exception as e:
        logger.error(f"处理小智端连接时发生错误: {e}")
    finally:
        await connection_manager.unregister_robot_connection(user_id)
        logger.info(f"小智端连接已关闭: {user_id}")


def signal_handler(signum, frame):
    """信号处理器"""
    logger.info(f"收到信号 {signum}，正在关闭服务器...")
    sys.exit(0)


def main():
    """主函数"""
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 获取配置
    host = config.get("server", "host", "127.0.0.1")
    port = config.getint("server", "port", 8004)
    debug = config.getboolean("server", "debug", False)

    logger.info(f"启动MCP Endpoint Server: {host}:{port}")

    # 启动服务器
    uvicorn.run(
        "src.server:app",
        host=host,
        port=port,
        reload=debug,
        log_level=config.get("server", "log_level", "INFO").lower(),
    )


if __name__ == "__main__":
    main()
