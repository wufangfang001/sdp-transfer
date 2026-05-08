"""
WebRTC 信令服务器配置
"""

# WS 服务配置（明文，用于本地测试）
WS_HOST = "0.0.0.0"
WS_PORT = 8765

# WSS 服务配置（加密，需要 SSL 证书）
WSS_HOST = "0.0.0.0"
WSS_PORT = 8766

# WHIP 服务配置（HTTP）
WHIP_HOST = "0.0.0.0"
WHIP_PORT = 8080

# WHIP 服务配置（HTTPS）
WHIPS_HOST = "0.0.0.0"
WHIPS_PORT = 8443

# WHIP 资源超时配置（秒）
WHIP_RESOURCE_TIMEOUT = 300  # 5 分钟无活动自动清理

# SSL 证书路径（由 generate_cert.py 生成）
SSL_CERT_FILE = "cert.pem"
SSL_KEY_FILE = "key.pem"

# STUN/TURN 服务器配置（供客户端使用，服务端仅透传给前端）
ICE_SERVERS = [
    {"urls": "stun:stun.l.google.com:19302"},
    {"urls": "stun:stun1.l.google.com:19302"},
    # 如需 TURN 服务器，取消注释并填写凭据：
    # {
    #     "urls": "turn:your-turn-server.com:3478",
    #     "username": "your-username",
    #     "credential": "your-password"
    # }
]

# 静态文件目录（Web Demo）
STATIC_DIR = "static"

# 日志级别
LOG_LEVEL = "INFO"
