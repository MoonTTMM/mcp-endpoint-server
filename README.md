# MCP Endpoint Server

一个高效的mcp接入点服务器，用于自定义mcp服务注册，方便拓展小智设备工具调用。

本项目是一个基于websocket的MCP注册中心，功能单一，建议使用Docker运行。

## 功能特性

- 🚀 **高性能**: 基于FastAPI和WebSocket的异步架构，支持高并发
- 🔄 **消息转发**: 自动转发工具端和小智端之间的消息
- 🔒 **连接管理**: 智能管理WebSocket连接，支持连接清理
- 📊 **监控统计**: 提供连接统计和健康检查接口
- ⚙️ **配置灵活**: 支持配置文件管理，易于部署和维护
- 🛡️ **错误处理**: 完善的错误处理和日志记录

## 架构设计

![原理图](./docs/schematic.png)

## docker运行

安装好docker后，拉取本项目源码

```bash
# 进入本项目源码根目录
cd mcp-endpoint-server

# 清除缓存
docker compose -f docker-compose.yml down
docker stop mcp-endpoint-server
docker rm mcp-endpoint-server
docker rmi ghcr.nju.edu.cn/xinnan-tech/mcp-endpoint-server:latest

# 启动docker容器
docker compose -f docker-compose.yml up -d
# 查看日志
docker logs -f mcp-endpoint-server
```

## 技术细节
[技术细节](./README_dev.md)