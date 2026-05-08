"""
WHIP 资源管理模块
管理 WHIP 会话资源的生命周期
"""

import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class WHIPResource:
    """WHIP 会话资源"""
    resource_id: str
    sdp_offer: str
    sdp_answer: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    last_activity: float = field(default_factory=time.time)
    
    def update_activity(self) -> None:
        """更新最后活动时间"""
        self.last_activity = time.time()


class WHIPResourceManager:
    """管理所有 WHIP 会话资源"""
    
    def __init__(self, timeout_seconds: int = 300):
        """
        初始化资源管理器
        
        Args:
            timeout_seconds: 资源超时时间（秒），默认 5 分钟
        """
        self._resources: Dict[str, WHIPResource] = {}
        self._timeout = timeout_seconds
        self._cleanup_task: Optional[asyncio.Task] = None
    
    def create_resource(self, sdp_offer: str) -> WHIPResource:
        """
        创建新的 WHIP 资源
        
        Args:
            sdp_offer: SDP Offer 内容
            
        Returns:
            创建的 WHIP 资源
        """
        resource_id = str(uuid.uuid4())
        resource = WHIPResource(
            resource_id=resource_id,
            sdp_offer=sdp_offer
        )
        self._resources[resource_id] = resource
        logger.info(f"[WHIP] 创建资源: {resource_id}")
        return resource
    
    def get_resource(self, resource_id: str) -> Optional[WHIPResource]:
        """
        获取 WHIP 资源
        
        Args:
            resource_id: 资源 ID
            
        Returns:
            WHIP 资源，不存在则返回 None
        """
        resource = self._resources.get(resource_id)
        if resource:
            resource.update_activity()
        return resource
    
    def delete_resource(self, resource_id: str) -> bool:
        """
        删除 WHIP 资源
        
        Args:
            resource_id: 资源 ID
            
        Returns:
            是否成功删除
        """
        if resource_id in self._resources:
            del self._resources[resource_id]
            logger.info(f"[WHIP] 删除资源: {resource_id}")
            return True
        return False
    
    def set_answer(self, resource_id: str, sdp_answer: str) -> bool:
        """
        设置 SDP Answer
        
        Args:
            resource_id: 资源 ID
            sdp_answer: SDP Answer 内容
            
        Returns:
            是否成功设置
        """
        resource = self._resources.get(resource_id)
        if resource:
            resource.sdp_answer = sdp_answer
            resource.update_activity()
            logger.info(f"[WHIP] 设置 Answer: {resource_id}")
            return True
        return False
    
    def start_cleanup_task(self) -> None:
        """启动超时清理任务"""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            logger.info("[WHIP] 超时清理任务已启动")
    
    def stop_cleanup_task(self) -> None:
        """停止超时清理任务"""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            logger.info("[WHIP] 超时清理任务已停止")
    
    async def _cleanup_loop(self) -> None:
        """定期清理超时资源"""
        while True:
            try:
                await asyncio.sleep(60)  # 每分钟检查一次
                self._cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[WHIP] 清理任务异常: {e}")
    
    def _cleanup_expired(self) -> int:
        """
        清理过期资源
        
        Returns:
            清理的资源数量
        """
        now = time.time()
        expired = [
            rid for rid, res in self._resources.items()
            if now - res.last_activity > self._timeout
        ]
        
        for rid in expired:
            del self._resources[rid]
            logger.info(f"[WHIP] 超时清理资源: {rid}")
        
        if expired:
            logger.info(f"[WHIP] 清理了 {len(expired)} 个过期资源")
        
        return len(expired)
    
    def stats(self) -> dict:
        """获取统计信息"""
        return {
            "active_resources": len(self._resources),
            "timeout_seconds": self._timeout,
        }
