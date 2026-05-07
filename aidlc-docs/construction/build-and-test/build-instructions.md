# 构建说明

## 前置条件
- Python 3.8+
- pip

## 构建步骤

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 生成 SSL 证书（WSS 支持）
```bash
python generate_cert.py
```
生成 `cert.pem` 和 `key.pem`，有效期 365 天。

### 3. 启动服务器
```bash
python signaling_server.py
```

预期输出：
```
WS  信令服务已启动: ws://0.0.0.0:8765
Web Demo 已启动:    http://localhost:8765/
WSS 信令服务已启动: wss://0.0.0.0:8766
```

### 4. 访问 Web Demo
浏览器打开 `http://localhost:8765/`

## 构建产物
| 文件 | 说明 |
|------|------|
| `cert.pem` | SSL 证书（运行时生成） |
| `key.pem` | SSL 私钥（运行时生成） |

## 常见问题

**端口被占用**：修改 `config.py` 中的 `WS_PORT` / `WSS_PORT`

**WSS 不启动**：先运行 `python generate_cert.py` 生成证书

**浏览器拒绝 WSS**：访问 `https://localhost:8766` 手动信任自签名证书
