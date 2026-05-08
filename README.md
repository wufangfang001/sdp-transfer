# WebRTC SDP 信令交换服务

基于 Python asyncio + websockets 实现的 WebRTC 信令服务器，完全兼容 WebRTC SDP/ICE 交互协议标准，同时支持 WS 和 WSS 连接，并附带完整的视频通话 Web Demo。

## 功能特性

- 支持 WS（明文）和 WSS（加密）双端口
- 完整的 SDP Offer/Answer 交换流程
- ICE Candidate 实时转发
- 一对一通话房间管理
- 内置 HTTP 静态文件服务（无需额外 Web 服务器）
- STUN/TURN 服务器配置支持
- 完整的视频通话 Web Demo
- WHIP/WHEP 协议支持（协议测试）

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 生成 SSL 证书（WSS 需要）

```bash
python generate_cert.py
```

> 生成 `cert.pem` 和 `key.pem`，有效期 365 天。

### 3. 启动服务器

```bash
python signaling_server.py
```

启动后输出：
```
WS  信令服务已启动: ws://0.0.0.0:8765
Web Demo 已启动:    http://localhost:8765/
WSS 信令服务已启动: wss://0.0.0.0:8766
```

### 4. 打开 Web Demo 测试

用**两个浏览器标签页**（或两台设备）访问：

```
http://localhost:8765/
```

**测试步骤**：
1. 两个标签页填写**相同的房间 ID**（如 `room-001`）
2. 两个标签页都点击「连接服务器」
3. 第一个连接的为**发起方（caller）**，第二个为**接听方（callee）**
4. 发起方点击「开始通话」
5. 双方视频建立后即可进行音视频通话

## WSS 连接测试

WSS 使用自签名证书，浏览器需要手动信任：

1. 访问 `https://localhost:8766`（注意是 HTTPS）
2. 点击「高级」→「继续访问 localhost（不安全）」
3. 回到 Demo 页面，将服务器地址改为 `wss://localhost:8766`

## 配置说明

编辑 `config.py` 修改配置：

```python
WS_PORT  = 8765   # WS 端口
WSS_PORT = 8766   # WSS 端口

# STUN/TURN 服务器（客户端使用）
ICE_SERVERS = [
    {"urls": "stun:stun.l.google.com:19302"},
    # TURN 服务器示例：
    # {
    #     "urls": "turn:your-turn-server.com:3478",
    #     "username": "user",
    #     "credential": "password"
    # }
]
```

## 信令协议

服务器使用 JSON 格式消息，完全兼容 WebRTC 标准信令流程：

| 消息类型 | 方向 | 说明 |
|----------|------|------|
| `join` | 客户端 → 服务器 | 加入房间 |
| `joined` | 服务器 → 客户端 | 加入成功，返回角色和 ICE 配置 |
| `peer-joined` | 服务器 → 客户端 | 对方已加入 |
| `peer-left` | 服务器 → 客户端 | 对方已离开 |
| `offer` | 客户端 ↔ 服务器 ↔ 客户端 | SDP Offer 转发 |
| `answer` | 客户端 ↔ 服务器 ↔ 客户端 | SDP Answer 转发 |
| `ice-candidate` | 客户端 ↔ 服务器 ↔ 客户端 | ICE Candidate 转发 |
| `leave` | 客户端 → 服务器 | 主动离开房间 |
| `error` | 服务器 → 客户端 | 错误通知 |

## 项目结构

```
.
├── signaling_server.py   # 主信令服务器
├── room_manager.py       # 房间管理模块
├── whip_server.py        # WHIP 协议服务器
├── whep_server.py        # WHEP 协议服务器
├── whip_resource_manager.py  # WHIP 资源管理
├── config.py             # 配置文件
├── generate_cert.py      # SSL 证书生成脚本
├── requirements.txt      # Python 依赖
├── README.md             # 本文档
└── static/
    ├── index.html        # Web Demo 主页面
    ├── app.js            # WebRTC 客户端逻辑
    └── style.css         # 样式文件
```

## 依赖

- Python 3.8+
- websockets 12.0
- cryptography 42.0.5
- aiohttp 3.9+

## WHIP/WHEP 协议支持

本项目提供 WHIP (WebRTC-HTTP Ingestion Protocol) 和 WHEP (WebRTC-HTTP Egress Protocol) 的基本实现，用于协议测试。

### 使用方式

在 Web Demo 中切换到「WHIP 推流」模式：
- **WHIP 推流**：发送本地摄像头视频流到服务器
- **WHEP 拉流**：从服务器请求视频流

### 重要限制

> **注意：当前 WHIP/WHEP 实现为协议层面的简化版本，仅用于测试 SDP 交换流程。**

**当前实现不包含：**
- 真正的 WebRTC 媒体引擎
- RTP 媒体包的接收和转发
- 媒体流的实际传输

**预期行为：**
- 推流端可以看到自己的本地视频（来自摄像头）
- 拉流端**不会看到远端画面**（因为服务器没有转发媒体流）

**如需完整的 WHIP/WHEP 功能，需要集成 WebRTC 媒体服务器，例如：**
- [MediaSoup](https://mediasoup.org/)
- [Janus](https://janus.conf.meetecho.com/)
- [Pion](https://pion.ly/)
- [GStreamer](https://gstreamer.freedesktop.org/)

### 完整视频通话测试

如需测试完整的视频通话功能，请使用「WebSocket 信令」模式：
1. 打开两个浏览器标签页
2. 都连接到同一个信令服务器
3. 输入相同的房间 ID
4. 一方点击「开始通话」
5. 双方即可进行音视频通话
