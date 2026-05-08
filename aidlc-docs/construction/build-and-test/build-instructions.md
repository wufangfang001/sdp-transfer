# 构建指令

## 前置要求
- **Python**: 3.8+
- **依赖管理**: pip
- **SSL 证书**: cert.pem, key.pem (可选，用于 HTTPS)

## 依赖安装

### 1. 安装 Python 依赖

```bash
pip install -r requirements.txt
pip install aiohttp
```

### 2. 生成 SSL 证书 (可选)

```bash
python generate_cert.py
```

## 构建

本项目为 Python 脚本，无需编译。

### 1. 验证代码语法

```bash
python -m py_compile signaling_server.py
python -m py_compile whip_server.py
python -m py_compile whip_resource_manager.py
python -m py_compile room_manager.py
python -m py_compile config.py
```

### 2. 验证导入

```bash
python -c "from whip_server import WHIPServer; print('OK')"
python -c "from whip_resource_manager import WHIPResourceManager; print('OK')"
python -c "from signaling_server import main; print('OK')"
```

## 启动服务

### 启动所有服务 (WebSocket + WHIP)

```bash
python signaling_server.py
```

### 预期输出

```
WS  信令服务已启动: ws://0.0.0.0:8765
Web Demo 已启动:    http://localhost:8765/
WSS 信令服务已启动: wss://0.0.0.0:8766
Web Demo (HTTPS) 已启动: https://localhost:8766/
WHIP HTTP 服务已启动: http://0.0.0.0:8080/whip/
WHIP HTTPS 服务已启动: https://0.0.0.0:8443/whip/
==================================================
所有服务已启动，按 Ctrl+C 停止
==================================================
```

## 端口配置

| 服务 | 端口 | 协议 |
|------|------|------|
| WebSocket | 8765 | WS |
| WebSocket Secure | 8766 | WSS |
| WHIP HTTP | 8080 | HTTP |
| WHIP HTTPS | 8443 | HTTPS |

## 故障排除

### SSL 证书错误
- **原因**: 证书文件不存在
- **解决**: 运行 `python generate_cert.py` 生成证书

### 端口被占用
- **原因**: 端口已被其他进程使用
- **解决**: 修改 `config.py` 中的端口配置

### 模块导入错误
- **原因**: 缺少依赖
- **解决**: `pip install aiohttp websockets`
