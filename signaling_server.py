"""
WebRTC SDP 信令交换服务器
支持 WS（明文）和 WSS（加密）双端口
完全兼容 WebRTC SDP/ICE 交互协议标准
"""

import asyncio
import json
import logging
import os
import ssl
import sys
from http import HTTPStatus
from pathlib import Path

import websockets
from websockets.server import WebSocketServerProtocol

from config import (
    ICE_SERVERS,
    SSL_CERT_FILE,
    SSL_KEY_FILE,
    STATIC_DIR,
    WS_HOST,
    WS_PORT,
    WSS_HOST,
    WSS_PORT,
)
from room_manager import RoomManager

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

room_manager = RoomManager()


# ---------------------------------------------------------------------------
# 消息处理
# ---------------------------------------------------------------------------

async def send_json(ws: WebSocketServerProtocol, data: dict) -> None:
    """发送 JSON 消息"""
    try:
        await ws.send(json.dumps(data))
    except websockets.exceptions.ConnectionClosed:
        pass


async def handle_join(ws: WebSocketServerProtocol, msg: dict) -> None:
    """处理客户端加入房间请求"""
    room_id = msg.get("room", "").strip()
    if not room_id:
        await send_json(ws, {"type": "error", "message": "room id 不能为空"})
        return

    logger.info(f"[handle_join] room_id={room_id}, ws={id(ws)}, current_stats={room_manager.stats()}")
    success, role = room_manager.join_room(room_id, ws)
    logger.info(f"[handle_join] success={success}, role={role}, new_stats={room_manager.stats()}")
    if not success:
        await send_json(ws, {"type": "error", "message": "房间已满（最多 2 人）"})
        return

    # 告知自身角色和 ICE 服务器配置
    await send_json(ws, {
        "type": "joined",
        "role": role,
        "room": room_id,
        "iceServers": ICE_SERVERS,
    })
    logger.info(f"客户端加入房间 {room_id}，角色: {role}")

    # 如果是第二个加入者，通知双方对方已就绪
    if role == "callee":
        peer = room_manager.get_peer(ws)
        if peer:
            await send_json(peer, {"type": "peer-joined"})
            await send_json(ws, {"type": "peer-joined"})


async def handle_offer(ws: WebSocketServerProtocol, msg: dict) -> None:
    """转发 SDP Offer 给对方"""
    room_id = room_manager.get_room_id(ws)
    logger.info(f"[handle_offer] room_id={room_id}, ws={id(ws)}, stats={room_manager.stats()}")
    peer = room_manager.get_peer(ws)
    logger.info(f"[handle_offer] peer={id(peer) if peer else None}")
    
    # 如果 get_peer 返回 None，尝试直接从房间获取
    if peer is None and room_id:
        room = room_manager._rooms.get(room_id)
        if room:
            # 如果当前 ws 是 caller，返回 callee；反之亦然
            if room.caller == ws:
                peer = room.callee
            elif room.callee == ws:
                peer = room.caller
            logger.info(f"[handle_offer] 从房间直接获取 peer={id(peer) if peer else None}")
    
    if peer is None:
        await send_json(ws, {"type": "error", "message": "对方尚未加入房间"})
        return
    sdp = msg.get("sdp")
    if not sdp:
        await send_json(ws, {"type": "error", "message": "offer 消息缺少 sdp 字段"})
        return
    await send_json(peer, {"type": "offer", "sdp": sdp})
    logger.info(f"[Room {room_id}] 转发 SDP Offer")


async def handle_answer(ws: WebSocketServerProtocol, msg: dict) -> None:
    """转发 SDP Answer 给对方"""
    peer = room_manager.get_peer(ws)
    if peer is None:
        await send_json(ws, {"type": "error", "message": "对方尚未加入房间"})
        return
    sdp = msg.get("sdp")
    if not sdp:
        await send_json(ws, {"type": "error", "message": "answer 消息缺少 sdp 字段"})
        return
    await send_json(peer, {"type": "answer", "sdp": sdp})
    logger.info(f"[Room {room_manager.get_room_id(ws)}] 转发 SDP Answer")


async def handle_ice_candidate(ws: WebSocketServerProtocol, msg: dict) -> None:
    """转发 ICE Candidate 给对方"""
    peer = room_manager.get_peer(ws)
    if peer is None:
        # 对方可能已断开，静默忽略
        return
    candidate = msg.get("candidate")
    if candidate is None:
        return
    await send_json(peer, {"type": "ice-candidate", "candidate": candidate})


async def handle_hangup(ws: WebSocketServerProtocol) -> None:
    """处理客户端挂断（不离开房间）"""
    room_id = room_manager.get_room_id(ws)
    logger.info(f"[handle_hangup] room_id={room_id}, ws={id(ws)}, stats={room_manager.stats()}")
    peer = room_manager.get_peer(ws)
    logger.info(f"[handle_hangup] peer={id(peer) if peer else None}")
    if peer:
        await send_json(peer, {"type": "peer-hangup"})
        logger.info("通知对方：peer-hangup")

async def handle_leave(ws: WebSocketServerProtocol) -> None:
    """处理客户端离开房间"""
    peer = room_manager.leave_room(ws)
    if peer:
        await send_json(peer, {"type": "peer-left"})
        logger.info("通知对方：peer-left")


# ---------------------------------------------------------------------------
# WebSocket 连接处理
# ---------------------------------------------------------------------------

async def signaling_handler(ws: WebSocketServerProtocol) -> None:
    """每个 WebSocket 连接的主处理循环"""
    remote = ws.remote_address
    protocol = "WSS" if ws.secure else "WS"
    logger.info(f"[{protocol}] 新连接: {remote}")

    try:
        async for raw in ws:
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await send_json(ws, {"type": "error", "message": "无效的 JSON 格式"})
                continue

            msg_type = msg.get("type", "")
            logger.debug(f"[{remote}] 收到消息类型: {msg_type}")

            if msg_type == "join":
                await handle_join(ws, msg)
            elif msg_type == "offer":
                await handle_offer(ws, msg)
            elif msg_type == "answer":
                await handle_answer(ws, msg)
            elif msg_type == "ice-candidate":
                await handle_ice_candidate(ws, msg)
            elif msg_type == "hangup":
                await handle_hangup(ws)
            elif msg_type == "leave":
                await handle_leave(ws)
            else:
                await send_json(ws, {"type": "error", "message": f"未知消息类型: {msg_type}"})

    except websockets.exceptions.ConnectionClosedOK:
        logger.info(f"[{protocol}] 连接正常关闭: {remote}")
    except websockets.exceptions.ConnectionClosedError as e:
        logger.warning(f"[{protocol}] 连接异常关闭: {remote} - {e}")
    finally:
        await handle_leave(ws)
        stats = room_manager.stats()
        logger.info(f"当前状态: {stats}")


# ---------------------------------------------------------------------------
# HTTP 静态文件服务（内嵌于 WS 服务器）
# ---------------------------------------------------------------------------

async def http_handler(path: str, request_headers) -> tuple | None:
    """
    处理 HTTP 请求，提供静态文件服务。
    WebSocket 升级请求（含 Upgrade: websocket 头）直接放行（返回 None）。
    """
    # WebSocket 升级请求：放行，交给 websockets 处理握手
    upgrade = request_headers.get("Upgrade", "")
    if upgrade.lower() == "websocket":
        return None

    static_root = Path(STATIC_DIR)

    # 规范化路径，防止目录遍历
    if path == "/" or path == "":
        file_path = static_root / "index.html"
    else:
        rel = path.lstrip("/")
        file_path = (static_root / rel).resolve()
        # 安全检查：确保路径在 static 目录内
        try:
            file_path.relative_to(static_root.resolve())
        except ValueError:
            return (HTTPStatus.FORBIDDEN, {}, b"Forbidden")

    if not file_path.exists() or not file_path.is_file():
        return (HTTPStatus.NOT_FOUND, {}, b"Not Found")

    content_types = {
        ".html": "text/html; charset=utf-8",
        ".js":   "application/javascript; charset=utf-8",
        ".css":  "text/css; charset=utf-8",
    }
    suffix = file_path.suffix.lower()
    content_type = content_types.get(suffix, "application/octet-stream")

    body = file_path.read_bytes()
    headers = {
        "Content-Type": content_type,
        "Content-Length": str(len(body)),
        "Cache-Control": "no-cache",
    }
    return (HTTPStatus.OK, headers, body)


# ---------------------------------------------------------------------------
# 服务器启动
# ---------------------------------------------------------------------------

def build_ssl_context() -> ssl.SSLContext | None:
    """构建 SSL 上下文，证书不存在时返回 None"""
    if not (os.path.exists(SSL_CERT_FILE) and os.path.exists(SSL_KEY_FILE)):
        logger.warning(
            f"SSL 证书文件不存在（{SSL_CERT_FILE} / {SSL_KEY_FILE}），"
            "WSS 服务将不会启动。请先运行: python generate_cert.py"
        )
        return None

    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(SSL_CERT_FILE, SSL_KEY_FILE)
    return ctx


async def main() -> None:
    ssl_ctx = build_ssl_context()

    # 启动 WS 服务（同时提供 HTTP 静态文件）
    ws_server = await websockets.serve(
        signaling_handler,
        WS_HOST,
        WS_PORT,
        process_request=http_handler,
    )
    logger.info(f"WS  信令服务已启动: ws://{WS_HOST}:{WS_PORT}")
    logger.info(f"Web Demo 已启动:    http://localhost:{WS_PORT}/")

    servers = [ws_server]

    # 启动 WSS 服务（仅信令，不提供静态文件）
    if ssl_ctx:
        wss_server = await websockets.serve(
            signaling_handler,
            WSS_HOST,
            WSS_PORT,
            ssl=ssl_ctx,
        )
        servers.append(wss_server)
        logger.info(f"WSS 信令服务已启动: wss://{WSS_HOST}:{WSS_PORT}")
    else:
        logger.info("WSS 服务未启动（缺少证书）")

    logger.info("按 Ctrl+C 停止服务")

    try:
        await asyncio.Future()  # 永久运行
    except asyncio.CancelledError:
        pass
    finally:
        for s in servers:
            s.close()
        await asyncio.gather(*[s.wait_closed() for s in servers])
        logger.info("服务已停止")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("收到中断信号，退出")
        sys.exit(0)
