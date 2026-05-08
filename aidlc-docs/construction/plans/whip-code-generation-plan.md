# WHIP 协议支持 - 代码生成计划

## 单元上下文

### 功能概述
为现有 WebSocket 信令服务器添加 WHIP (WebRTC-HTTP ingestion protocol) 支持，提供基于 HTTP 的 SDP 交换能力。

### 需求参考
- 需求文档: `aidlc-docs/inception/requirements/requirements.md`
- WHIP IETF Draft: https://www.ietf.org/archive/id/draft-ietf-wish-whip-01.html

### 技术决策
- **端口**: 独立端口 (HTTP:8080, HTTPS:8443)
- **认证**: 无
- **Trickle ICE**: 不支持
- **ICE Restart**: 不支持
- **资源管理**: 混合模式 (客户端删除 + 超时清理)
- **ICE 服务器配置**: 不返回

### 依赖关系
- 复用现有 SSL 证书 (cert.pem, key.pem)
- 独立于 WebSocket 信令服务

---

## 代码生成步骤

### Step 1: 更新配置文件
- [x] 修改 `config.py`，添加 WHIP 端口配置
- [x] 添加 WHIP 超时配置项

### Step 2: 创建 WHIP 资源管理器
- [x] 创建 `whip_resource_manager.py`
- [x] 实现 WHIPResource 类 (资源 ID、SDP、创建时间、WebRTC 连接状态)
- [x] 实现 WHIPResourceManager 类 (资源创建、查询、删除、超时清理)

### Step 3: 创建 WHIP HTTP 服务
- [x] 创建 `whip_server.py`
- [x] 实现 HTTP POST `/whip/` 端点处理
- [x] 实现 HTTP DELETE `/whip/<resource-id>` 端点处理
- [x] 实现 SDP Offer/Answer 处理逻辑
- [x] 实现错误响应处理

### Step 4: 集成到主服务器
- [x] 修改 `signaling_server.py`，添加 WHIP 服务启动逻辑
- [x] 实现 HTTP 和 HTTPS 双协议支持
- [x] 添加日志记录

### Step 5: 生成代码摘要文档
- [x] 创建 `aidlc-docs/construction/whip/code/whip-implementation-summary.md`
- [x] 记录实现细节和 API 使用说明

---

## 文件清单

### 需要修改的文件
| 文件 | 变更类型 | 说明 |
|------|----------|------|
| `config.py` | 修改 | 添加 WHIP 配置项 |
| `signaling_server.py` | 修改 | 添加 WHIP 服务启动 |

### 需要创建的文件
| 文件 | 说明 |
|------|------|
| `whip_resource_manager.py` | WHIP 资源管理模块 |
| `whip_server.py` | WHIP HTTP 服务处理 |

---

## API 规格

### POST /whip/
```
请求:
  Content-Type: application/sdp
  Body: SDP Offer (sendonly)

响应:
  201 Created
  Content-Type: application/sdp
  Location: /whip/{resource-id}
  Body: SDP Answer (recvonly)

错误:
  400 Bad Request - 无效的 SDP
  500 Internal Server Error - 服务器错误
```

### DELETE /whip/{resource-id}
```
响应:
  200 OK - 资源已删除
  404 Not Found - 资源不存在
```

---

## 预估工作量
- **总步骤数**: 5 个主要步骤
- **预估时间**: 15-20 分钟
