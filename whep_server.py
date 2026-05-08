"""
WHEP HTTP 服务模块
实现 WHEP 协议的 HTTP 端点处理 (拉流端)
"""

import asyncio
import logging
from http import HTTPStatus
from typing import Optional

from aiohttp import web

from config import WHIP_HOST, WHIP_PORT, WHIPS_HOST, WHIPS_PORT, WHIP_RESOURCE_TIMEOUT

logger = logging.getLogger(__name__)


class WHEPServer:
    """WHEP HTTP 服务器 (拉流端)"""
    
    def __init__(self):
        self._resources = {}  # resource_id -> SDP Offer (from WHIP)
        self._app: Optional[web.Application] = None
        self._runner: Optional[web.AppRunner] = None
    
    def set_whip_resources(self, resources: dict):
        """设置 WHIP 资源引用"""
        self._resources = resources
    
    async def handle_post_whep(self, request: web.Request) -> web.Response:
        """
        处理 POST /whep/ 请求
        创建新的 WHEP 会话 (拉流)
        
        WHEP 协议要求:
        - 请求: Content-Type: application/sdp, Body: SDP Offer (recvonly)
        - 响应: 201 Created, Content-Type: application/sdp, Location: /whep/{id}, Body: SDP Answer (sendonly)
        """
        content_type = request.headers.get("Content-Type", "")
        if not content_type.startswith("application/sdp"):
            return web.Response(
                status=HTTPStatus.BAD_REQUEST,
                text="Invalid Content-Type. Expected: application/sdp"
            )
        
        try:
            sdp_offer = await request.text()
        except Exception as e:
            logger.error(f"[WHEP] 读取请求体失败: {e}")
            return web.Response(
                status=HTTPStatus.BAD_REQUEST,
                text="Failed to read request body"
            )
        
        if not sdp_offer or not sdp_offer.strip():
            return web.Response(
                status=HTTPStatus.BAD_REQUEST,
                text="Empty SDP offer"
            )
        
        if not self._validate_sdp(sdp_offer):
            return web.Response(
                status=HTTPStatus.BAD_REQUEST,
                text="Invalid SDP format"
            )
        
        import uuid
        resource_id = str(uuid.uuid4())
        
        # 生成 SDP Answer
        sdp_answer = self._generate_answer(sdp_offer, resource_id)
        
        host = request.host.split(":")[0] if ":" in request.host else request.host
        scheme = request.scheme
        port = request.url.port if request.url.port else (443 if scheme == 'https' else 80)
        location = f"{scheme}://{host}:{port}/whep/{resource_id}"
        
        logger.info(f"[WHEP] POST /whep/ -> 201 Created, resource_id={resource_id}")
        
        return web.Response(
            status=HTTPStatus.CREATED,
            content_type="application/sdp",
            text=sdp_answer,
            headers={
                "Location": location,
                "Access-Control-Allow-Origin": "*",
            }
        )
    
    async def handle_delete_whep(self, request: web.Request) -> web.Response:
        """处理 DELETE /whep/{resource_id} 请求"""
        resource_id = request.match_info.get("resource_id", "")
        
        if not resource_id:
            return web.Response(
                status=HTTPStatus.BAD_REQUEST,
                text="Missing resource ID"
            )
        
        logger.info(f"[WHEP] DELETE /whep/{resource_id} -> 200 OK")
        
        return web.Response(
            status=HTTPStatus.OK,
            text="Resource deleted",
            headers={
                "Access-Control-Allow-Origin": "*",
            }
        )
    
    async def handle_options(self, request: web.Request) -> web.Response:
        """处理 OPTIONS 请求（CORS 预检）"""
        return web.Response(
            status=HTTPStatus.OK,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "POST, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
            }
        )
    
    def _validate_sdp(self, sdp: str) -> bool:
        """验证 SDP 基本格式"""
        required_fields = ["v=", "o=", "s=", "m="]
        return all(field in sdp for field in required_fields)
    
    def _generate_answer(self, offer: str, resource_id: str) -> str:
        """
        生成 SDP Answer (sendonly)
        WHEP 客户端发送 recvonly offer，服务器返回 sendonly answer
        """
        lines = offer.split("\n")
        answer_lines = []
        has_setup = False
        
        for line in lines:
            line = line.rstrip("\r")
            
            # 替换 recvonly 为 sendonly
            if "a=recvonly" in line:
                answer_lines.append("a=sendonly")
            # 替换 setup 属性
            elif line.startswith("a=setup:"):
                answer_lines.append("a=setup:passive")
                has_setup = True
            elif line.startswith("a=ice-ufrag:"):
                answer_lines.append(line)
            elif line.startswith("a=ice-pwd:"):
                answer_lines.append(line)
            elif line.startswith("a=fingerprint:"):
                answer_lines.append(line)
            elif line.startswith("a=candidate:"):
                answer_lines.append(line)
            elif line.startswith("a=mid:"):
                answer_lines.append(line)
                if not has_setup:
                    answer_lines.append("a=setup:passive")
                    has_setup = True
            elif line.startswith("m="):
                answer_lines.append(line)
            else:
                answer_lines.append(line)
        
        if not has_setup:
            for i, line in enumerate(answer_lines):
                if line.startswith("m="):
                    answer_lines.insert(i + 1, "a=setup:passive")
                    break
        
        return "\n".join(answer_lines)
    
    def create_app(self) -> web.Application:
        """创建 aiohttp 应用"""
        app = web.Application()
        
        app.router.add_route("POST", "/whep/", self.handle_post_whep)
        app.router.add_route("DELETE", "/whep/{resource_id}", self.handle_delete_whep)
        app.router.add_route("OPTIONS", "/whep/", self.handle_options)
        app.router.add_route("OPTIONS", "/whep/{resource_id}", self.handle_options)
        
        for path in ["/whep/", "/whep/{resource_id}"]:
            for method in ["GET", "HEAD", "PUT", "PATCH"]:
                app.router.add_route(method, path, self._handle_not_allowed)
        
        self._app = app
        return app
    
    async def _handle_not_allowed(self, request: web.Request) -> web.Response:
        return web.Response(
            status=HTTPStatus.METHOD_NOT_ALLOWED,
            text="Method not allowed",
            headers={
                "Allow": "POST, DELETE, OPTIONS",
                "Access-Control-Allow-Origin": "*",
            }
        )
    
    async def start(self, host: str, port: int, ssl_context=None) -> None:
        """启动 HTTP 服务"""
        if not self._app:
            self.create_app()
        
        self._runner = web.AppRunner(self._app)
        await self._runner.setup()
        
        site = web.TCPSite(self._runner, host, port, ssl_context=ssl_context)
        await site.start()
        
        protocol = "HTTPS" if ssl_context else "HTTP"
        logger.info(f"[WHEP] {protocol} 服务已启动: {host}:{port}")
    
    async def stop(self) -> None:
        """停止 HTTP 服务"""
        if self._runner:
            await self._runner.cleanup()
        logger.info("[WHEP] 服务已停止")
