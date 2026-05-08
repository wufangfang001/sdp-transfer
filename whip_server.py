"""
WHIP HTTP 服务模块
实现 WHIP 协议的 HTTP 端点处理
"""

import asyncio
import logging
import re
from http import HTTPStatus
from typing import Optional

from aiohttp import web

from config import WHIP_HOST, WHIP_PORT, WHIPS_HOST, WHIPS_PORT, WHIP_RESOURCE_TIMEOUT
from whip_resource_manager import WHIPResourceManager

logger = logging.getLogger(__name__)


class WHIPServer:
    """WHIP HTTP 服务器"""
    
    def __init__(self):
        self.resource_manager = WHIPResourceManager(timeout_seconds=WHIP_RESOURCE_TIMEOUT)
        self._app: Optional[web.Application] = None
        self._runner: Optional[web.AppRunner] = None
    
    async def handle_post_whip(self, request: web.Request) -> web.Response:
        """
        处理 POST /whip/ 请求
        创建新的 WHIP 会话
        
        WHIP 协议要求:
        - 请求: Content-Type: application/sdp, Body: SDP Offer (sendonly)
        - 响应: 201 Created, Content-Type: application/sdp, Location: /whip/{id}, Body: SDP Answer (recvonly)
        """
        # 验证 Content-Type
        content_type = request.headers.get("Content-Type", "")
        if not content_type.startswith("application/sdp"):
            return web.Response(
                status=HTTPStatus.BAD_REQUEST,
                text="Invalid Content-Type. Expected: application/sdp"
            )
        
        # 读取 SDP Offer
        try:
            sdp_offer = await request.text()
        except Exception as e:
            logger.error(f"[WHIP] 读取请求体失败: {e}")
            return web.Response(
                status=HTTPStatus.BAD_REQUEST,
                text="Failed to read request body"
            )
        
        if not sdp_offer or not sdp_offer.strip():
            return web.Response(
                status=HTTPStatus.BAD_REQUEST,
                text="Empty SDP offer"
            )
        
        # 验证 SDP 基本格式
        if not self._validate_sdp(sdp_offer):
            return web.Response(
                status=HTTPStatus.BAD_REQUEST,
                text="Invalid SDP format"
            )
        
        # 创建资源
        resource = self.resource_manager.create_resource(sdp_offer)
        
        # 生成 SDP Answer
        # 注意: 实际 WebRTC 场景中，这里需要与 WebRTC 媒体服务器交互
        # 当前简化实现：生成一个基本的 recvonly answer
        sdp_answer = self._generate_answer(sdp_offer, resource.resource_id)
        self.resource_manager.set_answer(resource.resource_id, sdp_answer)
        
        # 构建响应
        host = request.host.split(":")[0] if ":" in request.host else request.host
        scheme = request.scheme
        # aiohttp 的端口需要从 url 对象获取
        port = request.url.port if request.url.port else (443 if scheme == 'https' else 80)
        location = f"{scheme}://{host}:{port}/whip/{resource.resource_id}"
        
        logger.info(f"[WHIP] POST /whip/ -> 201 Created, resource_id={resource.resource_id}")
        
        return web.Response(
            status=HTTPStatus.CREATED,
            content_type="application/sdp",
            text=sdp_answer,
            headers={
                "Location": location,
                "Access-Control-Allow-Origin": "*",
            }
        )
    
    async def handle_delete_whip(self, request: web.Request) -> web.Response:
        """
        处理 DELETE /whip/{resource_id} 请求
        终止 WHIP 会话
        """
        resource_id = request.match_info.get("resource_id", "")
        
        if not resource_id:
            return web.Response(
                status=HTTPStatus.BAD_REQUEST,
                text="Missing resource ID"
            )
        
        resource = self.resource_manager.get_resource(resource_id)
        if not resource:
            return web.Response(
                status=HTTPStatus.NOT_FOUND,
                text="Resource not found"
            )
        
        self.resource_manager.delete_resource(resource_id)
        logger.info(f"[WHIP] DELETE /whip/{resource_id} -> 200 OK")
        
        return web.Response(
            status=HTTPStatus.OK,
            text="Resource deleted",
            headers={
                "Access-Control-Allow-Origin": "*",
            }
        )
    
    async def handle_options(self, request: web.Request) -> web.Response:
        """
        处理 OPTIONS 请求（CORS 预检）
        """
        return web.Response(
            status=HTTPStatus.OK,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
            }
        )
    
    async def handle_not_allowed(self, request: web.Request) -> web.Response:
        """
        处理不支持的 HTTP 方法
        WHIP 规范要求返回 405
        """
        return web.Response(
            status=HTTPStatus.METHOD_NOT_ALLOWED,
            text="Method not allowed",
            headers={
                "Allow": "POST, DELETE, OPTIONS",
                "Access-Control-Allow-Origin": "*",
            }
        )
    
    def _validate_sdp(self, sdp: str) -> bool:
        """验证 SDP 基本格式"""
        # 检查是否包含必要的 SDP 字段
        required_fields = ["v=", "o=", "s=", "m="]
        return all(field in sdp for field in required_fields)
    
    def _generate_answer(self, offer: str, resource_id: str) -> str:
        """
        生成 SDP Answer
        
        注意: 这是一个简化实现
        实际生产环境需要:
        1. 解析 Offer 中的媒体行
        2. 与 WebRTC 媒体引擎交互
        3. 生成匹配的 Answer
        """
        lines = offer.split("\n")
        answer_lines = []
        
        for line in lines:
            line = line.rstrip("\r")
            
            # 替换 sendonly 为 recvonly
            if "a=sendonly" in line:
                answer_lines.append("a=recvonly")
            # 复制其他行
            elif line.startswith("a=ice-ufrag:"):
                # 保持 ICE ufrag
                answer_lines.append(line)
            elif line.startswith("a=ice-pwd:"):
                # 保持 ICE pwd
                answer_lines.append(line)
            elif line.startswith("a=fingerprint:"):
                # 保持 fingerprint
                answer_lines.append(line)
            elif line.startswith("a=candidate:"):
                # 保持 candidates
                answer_lines.append(line)
            else:
                answer_lines.append(line)
        
        return "\n".join(answer_lines)
    
    def create_app(self) -> web.Application:
        """创建 aiohttp 应用"""
        app = web.Application()
        
        # 路由配置
        app.router.add_route("POST", "/whip/", self.handle_post_whip)
        app.router.add_route("DELETE", "/whip/{resource_id}", self.handle_delete_whip)
        app.router.add_route("OPTIONS", "/whip/", self.handle_options)
        app.router.add_route("OPTIONS", "/whip/{resource_id}", self.handle_options)
        
        # 其他方法返回 405
        for path in ["/whip/", "/whip/{resource_id}"]:
            for method in ["GET", "HEAD", "PUT", "PATCH"]:
                app.router.add_route(method, path, self.handle_not_allowed)
        
        self._app = app
        return app
    
    async def start(self, host: str, port: int, ssl_context=None) -> None:
        """启动 HTTP 服务"""
        if not self._app:
            self.create_app()
        
        self._runner = web.AppRunner(self._app)
        await self._runner.setup()
        
        site = web.TCPSite(self._runner, host, port, ssl_context=ssl_context)
        await site.start()
        
        # 启动资源清理任务
        self.resource_manager.start_cleanup_task()
        
        protocol = "HTTPS" if ssl_context else "HTTP"
        logger.info(f"[WHIP] {protocol} 服务已启动: {host}:{port}")
    
    async def stop(self) -> None:
        """停止 HTTP 服务"""
        self.resource_manager.stop_cleanup_task()
        
        if self._runner:
            await self._runner.cleanup()
        
        logger.info("[WHIP] 服务已停止")


async def create_whip_servers(ssl_context=None) -> tuple:
    """
    创建 WHIP HTTP 和 HTTPS 服务器
    
    Returns:
        (http_server, https_server)
    """
    http_server = WHIPServer()
    https_server = WHIPServer() if ssl_context else None
    
    return http_server, https_server
