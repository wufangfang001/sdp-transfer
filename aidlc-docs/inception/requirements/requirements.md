# WHIP 协议支持 - 需求文档

## 意图分析

| 维度 | 评估 |
|------|------|
| **用户请求** | 为现有 WebRTC 信令服务器添加 WHIP 协议支持 |
| **请求类型** | 新功能 |
| **范围估计** | 单组件扩展 |
| **复杂度估计** | 中等 (简化实现) |

## 功能概述

WHIP (WebRTC-HTTP ingestion protocol) 是一种基于 HTTP 的 WebRTC 媒体注入协议，允许编码器/媒体生产者通过简单的 HTTP POST 请求建立 WebRTC 会话。

## 功能需求

### FR-01: WHIP 端点创建 (HTTP POST)
- **描述**: 提供 WHIP 端点 URL，接收 SDP Offer
- **HTTP 方法**: POST
- **路径**: `/whip/`
- **请求头**: `Content-Type: application/sdp`
- **请求体**: SDP Offer (sendonly)
- **响应**: 
  - 状态码: 201 Created
  - 响应头: 
    - `Content-Type: application/sdp`
    - `Location: <WHIP 资源 URL>`
  - 响应体: SDP Answer (recvonly)

### FR-02: WHIP 会话终止 (HTTP DELETE)
- **描述**: 终止 WHIP 会话，释放资源
- **HTTP 方法**: DELETE
- **路径**: `/whip/<resource-id>`
- **响应**: 
  - 状态码: 200 OK

### FR-03: 独立端口服务
- **描述**: WHIP 服务使用独立的 HTTP/HTTPS 端口
- **配置**:
  - HTTP 端口: 8080 (可配置)
  - HTTPS 端口: 8443 (可配置)

### FR-04: HTTP 和 HTTPS 支持
- **描述**: 同时支持 HTTP 和 HTTPS 访问
- **HTTPS**: 复用现有 SSL 证书 (cert.pem, key.pem)

### FR-05: 资源生命周期管理
- **描述**: 管理 WHIP 会话资源的生命周期
- **机制**:
  - 客户端主动删除: HTTP DELETE
  - 超时自动清理: 无活动超时后自动清理 (默认 5 分钟)

### FR-06: 错误处理
- **描述**: 提供标准的 HTTP 错误响应
- **错误码**:
  - 400 Bad Request: 无效的 SDP 或请求格式
  - 404 Not Found: 资源不存在
  - 405 Method Not Allowed: 不支持的 HTTP 方法
  - 500 Internal Server Error: 服务器内部错误

## 非功能需求

### NFR-01: 性能
- 单服务器支持至少 100 个并发 WHIP 会话
- SDP 交换响应时间 < 100ms

### NFR-02: 可靠性
- 资源清理机制确保无内存泄漏
- 异常情况下正确释放资源

### NFR-03: 可维护性
- 代码模块化，WHIP 逻辑独立于 WebSocket 信令
- 清晰的日志记录

## 技术约束

### TC-01: 简化实现
以下功能不实现，以简化开发：
- ❌ 认证机制 (Bearer Token)
- ❌ Trickle ICE (HTTP PATCH)
- ❌ ICE Restart
- ❌ ICE 服务器配置返回

### TC-02: 协议兼容性
- SDP Offer 应包含 `sendonly` 属性
- SDP Answer 应包含 `recvonly` 属性
- 支持 BUNDLE 和 RTCP mux

## 与现有系统的关系

| 组件 | 关系 |
|------|------|
| WebSocket 信令服务 | 独立运行，互不干扰 |
| 房间管理 (RoomManager) | 不复用，WHIP 有独立的会话管理 |
| 配置文件 (config.py) | 扩展配置项 |
| SSL 证书 | 复用现有证书文件 |

## 实现范围

### 需要修改的文件
- `config.py`: 添加 WHIP 端口配置
- `signaling_server.py`: 添加 WHIP HTTP 服务

### 需要新增的文件
- `whip_resource_manager.py`: WHIP 资源管理模块

### 测试方式
- 使用 `curl` 命令测试 HTTP API
- 使用 `ffmpeg` 进行实际的 WHIP 推流测试

## 参考
- [WHIP IETF Draft](https://www.ietf.org/archive/id/draft-ietf-wish-whip-01.html)
