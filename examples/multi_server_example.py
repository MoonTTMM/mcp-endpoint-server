#!/usr/bin/env python3
"""
多服务器MCP使用示例
演示如何连接多个MCP服务器并使用统一接口
"""

import asyncio
import json
import websockets
from urllib.parse import quote

# 服务器配置
SERVER_HOST = "localhost"
SERVER_PORT = 8004
SERVER_KEY = "your_server_key"  # 请替换为实际的服务器密钥

# 智能体配置
AGENT_ID = "example_agent"
SERVER_CONFIGS = [
    {"server_id": "calculator_server", "tools": ["calculator", "scientific_calculator"]},
    {"server_id": "weather_server", "tools": ["weather", "forecast"]},
    {"server_id": "translator_server", "tools": ["translate", "detect_language"]}
]


async def connect_mcp_server(agent_id: str, server_id: str, tools: list):
    """连接MCP服务器"""
    # 生成token
    token_data = {"agentId": agent_id}
    token = quote(json.dumps(token_data))
    
    # 构建WebSocket URL，包含server_id参数
    uri = f"ws://{SERVER_HOST}:{SERVER_PORT}/mcp_endpoint/mcp/?token={token}&server_id={server_id}"
    
    try:
        websocket = await websockets.connect(uri)
        print(f"[{agent_id}/{server_id}] 已连接到MCP Endpoint Server")
        
        # 发送初始化消息
        init_message = {
            "id": 0,
            "jsonrpc": "2.0",
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "sampling": {},
                    "roots": {"listChanged": False}
                },
                "clientInfo": {
                    "name": f"example-mcp-{server_id}",
                    "version": "1.0.0"
                }
            }
        }
        
        await websocket.send(json.dumps(init_message))
        response = await websocket.recv()
        print(f"[{agent_id}/{server_id}] 初始化完成")
        
        # 发送工具列表
        tools_message = {
            "id": 1,
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {}
        }
        
        await websocket.send(json.dumps(tools_message))
        response = await websocket.recv()
        print(f"[{agent_id}/{server_id}] 工具列表已发送")
        
        return websocket
        
    except Exception as e:
        print(f"[{agent_id}/{server_id}] 连接失败: {e}")
        return None


async def handle_tool_calls(websocket, agent_id: str, server_id: str):
    """处理工具调用"""
    try:
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            
            if data.get("method") == "tools/call":
                params = data.get("params", {})
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                request_id = data.get("id")
                
                print(f"[{agent_id}/{server_id}] 收到工具调用: {tool_name}")
                
                # 模拟工具执行
                result = f"来自 {agent_id}/{server_id} 的工具 {tool_name} 执行结果"
                
                response = {
                    "jsonrpc": "2.0",
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": result
                            }
                        ]
                    },
                    "id": request_id
                }
                
                await websocket.send(json.dumps(response))
                print(f"[{agent_id}/{server_id}] 工具调用完成")
                
    except websockets.exceptions.ConnectionClosed:
        print(f"[{agent_id}/{server_id}] 连接已关闭")
    except Exception as e:
        print(f"[{agent_id}/{server_id}] 处理消息时发生错误: {e}")


async def robot_client_example():
    """小智端客户端示例"""
    # 生成token
    token_data = {"agentId": AGENT_ID}
    token = quote(json.dumps(token_data))
    
    uri = f"ws://{SERVER_HOST}:{SERVER_PORT}/mcp_endpoint/call/?token={token}"
    
    try:
        websocket = await websockets.connect(uri)
        print(f"[Robot-{AGENT_ID}] 已连接到MCP Endpoint Server")
        
        # 获取工具列表
        tools_message = {
            "id": 1,
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {}
        }
        
        await websocket.send(json.dumps(tools_message))
        response = await websocket.recv()
        data = json.loads(response)
        
        if "result" in data:
            tools = data["result"].get("tools", [])
            print(f"[Robot-{AGENT_ID}] 获取到 {len(tools)} 个工具:")
            for tool in tools:
                print(f"  - {tool['name']} (来自: {tool.get('server_id', 'unknown')})")
        
        # 测试工具调用
        test_tools = ["calculator", "weather", "translate"]
        for tool_name in test_tools:
            call_message = {
                "id": 10,
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": {
                        "test": "参数"
                    }
                }
            }
            
            await websocket.send(json.dumps(call_message))
            response = await websocket.recv()
            data = json.loads(response)
            
            if "result" in data:
                print(f"[Robot-{AGENT_ID}] 工具 {tool_name} 调用成功")
            else:
                print(f"[Robot-{AGENT_ID}] 工具 {tool_name} 调用失败: {data.get('error', {})}")
            
            await asyncio.sleep(1)
        
        await websocket.close()
        
    except Exception as e:
        print(f"[Robot-{AGENT_ID}] 连接失败: {e}")


async def main():
    """主函数"""
    print("=== 多服务器MCP示例 ===")
    print(f"智能体ID: {AGENT_ID}")
    print(f"服务器配置: {len(SERVER_CONFIGS)} 个服务器")
    
    # 启动所有服务器
    server_tasks = []
    for server_config in SERVER_CONFIGS:
        websocket = await connect_mcp_server(
            AGENT_ID, 
            server_config["server_id"], 
            server_config["tools"]
        )
        if websocket:
            task = asyncio.create_task(
                handle_tool_calls(websocket, AGENT_ID, server_config["server_id"])
            )
            server_tasks.append(task)
    
    if not server_tasks:
        print("没有服务器成功连接")
        return
    
    print(f"成功启动 {len(server_tasks)} 个MCP服务器")
    
    # 等待一段时间让服务器完成初始化
    await asyncio.sleep(2)
    
    # 运行小智端客户端示例
    await robot_client_example()
    
    print("=== 示例完成 ===")
    
    # 取消所有任务
    for task in server_tasks:
        task.cancel()


if __name__ == "__main__":
    asyncio.run(main()) 