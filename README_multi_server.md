# MCP Endpoint Server - 多服务器支持

## 概述

MCP Endpoint Server 现在支持连接多个MCP服务器，并能够统一管理和调用来自不同服务器的工具。这个功能允许您：

- 连接多个MCP服务器到同一个智能体
- 获取智能体的所有工具列表
- 根据工具名称自动路由到正确的服务器
- 统一管理多个服务器的连接状态
- 支持工具列表请求和智能工具调用

## 架构设计

### 核心概念

- **agent_id**: 标识一个智能体，一个智能体可以连接多个MCP服务器
- **server_id**: 标识具体的MCP服务器，用于区分同一智能体下的不同服务器
- **工具路由**: 根据工具名称自动找到对应的服务器进行调用

### 连接结构

```
智能体 (agent_id: "my_agent")
├── MCP服务器1 (server_id: "calculator_server")
│   ├── 工具: calculator, scientific_calculator
│   └── 连接: WebSocket
├── MCP服务器2 (server_id: "weather_server")  
│   ├── 工具: weather, forecast
│   └── 连接: WebSocket
└── MCP服务器3 (server_id: "translator_server")
    ├── 工具: translate, detect_language
    └── 连接: WebSocket
```

## 功能特性

### 多服务器连接

```python
# 连接多个MCP服务器到同一个智能体
# 智能体: agent_id = "my_agent"
# 服务器1: server_id = "calculator_server"
# 服务器2: server_id = "weather_server"  
# 服务器3: server_id = "translator_server"
```

### 统一工具列表

当小智端请求工具列表时，系统会返回该智能体的所有工具：

```json
{
  "jsonrpc": "2.0",
  "result": {
    "tools": [
      {
        "name": "calculator",
        "description": "数学计算器",
        "server_id": "calculator_server"
      },
      {
        "name": "weather",
        "description": "天气查询", 
        "server_id": "weather_server"
      },
      {
        "name": "translate",
        "description": "翻译工具",
        "server_id": "translator_server"
      }
    ]
  },
  "id": 1
}
```

### 智能工具调用

当小智端调用工具时，系统会自动找到对应的服务器：

```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "calculator",
    "arguments": {
      "expression": "2 + 3 * 4"
    }
  },
  "id": 10
}
```

系统会自动将请求路由到 `calculator_server`。

### 聚合响应

当小智端发送广播消息时，系统会收集所有MCP服务器的响应并聚合后统一发送：

```json
{
  "jsonrpc": "2.0",
  "method": "broadcast",
  "params": {
    "message": "Hello from broadcast test!"
  },
  "id": 20
}
```

聚合响应示例：

```json
{
  "jsonrpc": "2.0",
  "id": 20,
  "result": {
    "responses": [
      {
        "content": [{"type": "text", "text": "来自 calculator_server 的响应"}],
        "server_id": "calculator_server"
      },
      {
        "content": [{"type": "text", "text": "来自 weather_server 的响应"}],
        "server_id": "weather_server"
      },
      {
        "content": [{"type": "text", "text": "来自 translator_server 的响应"}],
        "server_id": "translator_server"
      }
    ],
    "total_servers": 3,
    "responded_servers": 3
  }
}
```

## API接口

### 1. 健康检查接口

获取多服务器统计信息：

```bash
GET /mcp_endpoint/health?key=your_server_key
```

响应示例：

```json
{
  "jsonrpc": "2.0",
  "result": {
    "status": "success",
    "connections": {
      "mcp_server_connections": 3,
      "robot_connections": 1,
      "total_connections": 4,
      "multi_server_support": true,
      "available_agents": ["my_agent"],
      "total_tools": 6,
      "mcp_servers": {
        "my_agent": {
          "calculator_server": {
            "tools_count": 2,
            "tools": ["calculator", "scientific_calculator"],
            "server_info": {...}
          },
          "weather_server": {
            "tools_count": 1,
            "tools": ["weather"],
            "server_info": {...}
          }
        }
      }
    }
  },
  "id": null
}
```

### 2. WebSocket接口

#### MCP服务器连接

```bash
# 格式
ws://host:port/mcp_endpoint/mcp/?token=your_token&server_id=your_server_id

# 示例
ws://localhost:8004/mcp_endpoint/mcp/?token=my_agent_token&server_id=calculator_server
```

#### 小智端连接

```bash
# 格式
ws://host:port/mcp_endpoint/call/?token=your_token

# 示例
ws://localhost:8004/mcp_endpoint/call/?token=my_agent_token
```

#### 工具列表请求（通过WebSocket）

小智端可以通过WebSocket请求工具列表：

```json
{
  "id": 1,
  "jsonrpc": "2.0",
  "method": "tools/list",
  "params": {}
}
```

响应示例：

```json
{
  "jsonrpc": "2.0",
  "result": {
    "tools": [
      {
        "name": "calculator",
        "description": "数学计算器",
        "server_id": "calculator_server"
      },
      {
        "name": "weather",
        "description": "天气查询",
        "server_id": "weather_server"
      }
    ]
  },
  "id": 1
}
```

#### 工具调用请求（通过WebSocket）

小智端可以通过WebSocket调用工具：

```json
{
  "id": 10,
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "calculator",
    "arguments": {
      "expression": "2 + 3 * 4"
    }
  }
}
```

系统会自动将请求路由到对应的MCP服务器。

## 部署示例

### 1. 启动MCP Endpoint Server

```bash
python main.py
```

### 2. 连接多个MCP服务器

使用相同的agent_id但不同的server_id连接多个服务器：

```bash
# 服务器1 - 计算器服务
ws://localhost:8004/mcp_endpoint/mcp/?token=my_agent_token&server_id=calculator_server

# 服务器2 - 天气服务  
ws://localhost:8004/mcp_endpoint/mcp/?token=my_agent_token&server_id=weather_server

# 服务器3 - 翻译服务
ws://localhost:8004/mcp_endpoint/mcp/?token=my_agent_token&server_id=translator_server
```

### 3. 小智端连接

```bash
ws://localhost:8004/mcp_endpoint/call/?token=my_agent_token
```

### 4. 测试功能

```bash
# 获取工具列表
{
  "id": 1,
  "jsonrpc": "2.0",
  "method": "tools/list",
  "params": {}
}

# 调用工具
{
  "id": 10,
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "calculator",
    "arguments": {
      "expression": "2 + 3 * 4"
    }
  }
}
```

## 测试

运行测试脚本验证多服务器功能：

```bash
python test_multi_server.py
```

测试脚本会：

1. 启动3个模拟MCP服务器（同一智能体）
2. 连接小智端客户端
3. 获取统一工具列表
4. 测试工具调用路由
5. 验证聚合响应功能

## 错误处理

### 工具不存在

当请求的工具不存在时：

```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32601,
    "message": "工具 'nonexistent_tool' 不存在"
  },
  "id": 10
}
```

### 服务器未连接

当工具对应的服务器未连接时：

```json
{
  "jsonrpc": "2.0", 
  "error": {
    "code": -32001,
    "message": "MCP服务器 'calculator_server' 未连接"
  },
  "id": 10
}
```

### 转发失败

当转发消息失败时：

```json
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32002,
    "message": "转发工具调用请求失败"
  },
  "id": 10
}
```

## 配置说明

### 服务器配置

在 `mcp-endpoint-server.cfg` 中：

```ini
[server]
host = 0.0.0.0
port = 8004
debug = false
log_level = INFO

[security]
allowed_origins = *
enable_cors = true
```

### 连接限制

- 每个智能体可以连接多个MCP服务器
- 每个server_id在同一智能体下只能有一个活跃连接
- 支持多个小智端同时连接
- 自动清理断开的连接

## 监控和日志

### 连接统计

通过健康检查接口可以监控：

- 活跃的MCP服务器连接数
- 活跃的小智端连接数
- 每个智能体的服务器数量
- 每个服务器的工具数量
- 总工具数量

### 日志记录

系统会记录：

- 服务器连接/断开事件
- 工具列表更新
- 工具调用路由
- 聚合响应处理
- 错误和异常

## 性能考虑

- 使用异步处理提高并发性能
- 连接池管理减少资源消耗
- 智能路由避免不必要的消息转发
- 自动清理断开的连接
- 聚合响应优化减少网络开销

## 扩展性

系统设计支持：

- 动态添加/移除MCP服务器
- 负载均衡和故障转移
- 自定义路由策略
- 插件化工具管理
- 自定义聚合策略

## 故障排除

### 常见问题

1. **工具调用失败**
   - 检查工具名称是否正确
   - 确认对应的服务器是否连接
   - 查看服务器日志

2. **连接断开**
   - 检查网络连接
   - 确认token是否正确
   - 查看服务器状态

3. **工具列表为空**
   - 确认MCP服务器已发送工具列表
   - 检查初始化是否成功
   - 查看连接状态

4. **聚合响应超时**
   - 检查所有服务器是否响应
   - 确认网络连接稳定
   - 查看超时配置

### 调试模式

启用调试模式获取详细日志：

```ini
[server]
debug = true
log_level = DEBUG
```

### 日志级别

- `DEBUG`: 详细调试信息
- `INFO`: 一般信息
- `WARNING`: 警告信息
- `ERROR`: 错误信息 