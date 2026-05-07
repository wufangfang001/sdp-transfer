# 代码生成计划 - WebRTC 信令服务器

## 单元信息
- **单元名称**: signaling-server
- **项目类型**: 绿地项目
- **技术栈**: Python 3.8+ / asyncio / websockets / HTML5 / JavaScript

## 用户故事覆盖
- [x] US-01: 启动信令服务器
- [x] US-02: 客户端通过 WebSocket 连接并交换 SDP
- [x] US-03: Web Demo 页面测试通话
- [x] US-04: WSS 安全连接
- [x] US-05: 音视频通话验证

## 依赖关系
- 无外部单元依赖（单一单元项目）
- Python 依赖: websockets, asyncio (标准库), ssl (标准库)

---

## 代码生成步骤

### Step 1: 项目结构初始化 ✅
- [x] 创建工作区根目录结构
- [x] 创建 `requirements.txt`
- [x] 创建 `config.py` 配置文件

### Step 2: SSL 证书生成脚本 ✅
- [x] 创建 `generate_cert.py`
- [x] 使用 Python cryptography 库生成自签名证书

### Step 3: 房间管理模块 ✅
- [x] 创建 `room_manager.py`
- [x] 实现一对一通话配对逻辑
- [x] 管理客户端连接状态
- [x] 处理客户端断开清理

### Step 4: 主信令服务器 ✅
- [x] 创建 `signaling_server.py`
- [x] 实现 WebSocket 消息处理
- [x] 实现 SDP Offer/Answer 转发
- [x] 实现 ICE Candidate 转发
- [x] 支持 WS 和 WSS 双端口监听
- [x] 集成房间管理模块

### Step 5: Web Demo 样式 ✅
- [x] 创建 `static/` 目录
- [x] 创建 `static/style.css` 样式文件

### Step 6: Web Demo JavaScript 客户端 ✅
- [x] 创建 `static/app.js`
- [x] 实现 WebSocket 连接管理
- [x] 实现 RTCPeerConnection 创建和管理
- [x] 实现 SDP Offer/Answer 创建和处理
- [x] 实现 ICE Candidate 收集和交换
- [x] 实现本地/远端媒体流管理
- [x] 实现 STUN/TURN 配置

### Step 7: Web Demo HTML 页面 ✅
- [x] 创建 `static/index.html`
- [x] 本地视频预览区域
- [x] 远端视频显示区域
- [x] 连接控制按钮
- [x] 房间 ID 输入
- [x] 状态显示区域

### Step 8: 项目文档 ✅
- [x] 创建 `README.md`
- [x] 包含安装说明
- [x] 包含启动步骤
- [x] 包含使用说明
- [x] 包含 STUN/TURN 配置说明

---

## 最终文件结构
```
<workspace-root>/
├── signaling_server.py      ✅
├── room_manager.py          ✅
├── config.py                ✅
├── generate_cert.py         ✅
├── requirements.txt         ✅
├── README.md                ✅
└── static/
    ├── index.html           ✅
    ├── app.js               ✅
    └── style.css            ✅
```

## 完成状态: 全部完成 ✅
