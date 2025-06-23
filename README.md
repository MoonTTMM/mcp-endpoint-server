# MCP Endpoint Server

一个高效的mcp接入点服务器，用于自定义mcp服务注册，方便拓展小智设备工具调用。

## 功能特性

- 🚀 **高性能**: 基于FastAPI和WebSocket的异步架构，支持高并发
- 🔄 **消息转发**: 自动转发工具端和小智端之间的消息
- 🔒 **连接管理**: 智能管理WebSocket连接，支持连接清理
- 📊 **监控统计**: 提供连接统计和健康检查接口
- ⚙️ **配置灵活**: 支持配置文件管理，易于部署和维护
- 🛡️ **错误处理**: 完善的错误处理和日志记录

## 架构设计

```
小智端项目 ──→ WebSocket服务器 ──→ 工具端
     ↑                    ↓                    ↑
     └─── 消息转发 ───────┴─── 消息转发 ───────┘
```

## 安装依赖

```bash
conda remove -n mcp-endpoint-server --all -y
conda create -n mcp-endpoint-server python=3.10 -y
conda activate mcp-endpoint-server

pip install -r requirements.txt

cp mcp-endpoint-server.cfg data/.mcp-endpoint-server.cfg

```

## 配置说明

### 配置文件位置
- 示例配置: `mcp-endpoint-server.cfg`
- 实际配置: `data/.mcp-endpoint-server.cfg`

### 配置项说明

```ini
[server]
host = 127.0.0.1          # 服务器监听地址
port = 8004               # 服务器监听端口
debug = false             # 调试模式
log_level = INFO          # 日志级别

[websocket]
max_connections = 1000    # 最大连接数
ping_interval = 30        # 心跳间隔(秒)
ping_timeout = 10         # 心跳超时(秒)
close_timeout = 10        # 关闭超时(秒)

[security]
allowed_origins = *       # 允许的源
enable_cors = true        # 启用CORS

[logging]
log_file = logs/mcp_server.log  # 日志文件路径
max_file_size = 10MB            # 日志文件最大大小
backup_count = 5                # 日志备份数量
```

## 启动服务器

```bash
python main.py
```

### 测试数据
```json
{"id":0,"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{"sampling":{},"roots":{"listChanged":false}},"clientInfo":{"name":"xz-mcp-broker","version":"0.0.1"}}}


{"jsonrpc":"2.0","method":"notifications/initialized"}


{"id":1,"jsonrpc":"2.0","method":"tools/list","params":{}}


{"id":2,"jsonrpc":"2.0","method":"ping","params":{}}


{"id":10,"jsonrpc":"2.0","method":"tools/call","params":{"name":"calculator","arguments":{"python_expression":"130000 * 130000"},"serialNumber":null}}
```

### Docker部署

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8004

CMD ["python", "main.py"]
```

## 监控和维护

### 日志查看
```bash
tail -f logs/mcp_server.log
```

### 连接状态检查
```bash
curl http://127.0.0.1:8004/stats
```

### 健康检查
```bash
curl http://127.0.0.1:8004/health
```

## 开发说明

### 项目结构
```
mcp-endpoint-server/
├── src/
│   ├── core/                 # 核心模块
│   │   └── connection_manager.py
│   ├── handlers/             # 处理器
│   │   └── websocket_handler.py
│   ├── utils/                # 工具模块
│   │   ├── config.py
│   │   └── logger.py
│   └── server.py             # 主服务器
├── data/                     # 配置文件目录
├── logs/                     # 日志目录
├── main.py                   # 主入口
├── requirements.txt          # 依赖文件
└── README.md                 # 说明文档
```
