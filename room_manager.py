"""
房间管理模块 - 一对一通话配对
"""

import logging
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class Room:
    """表示一个一对一通话房间，最多容纳两个客户端"""

    def __init__(self, room_id: str):
        self.room_id = room_id
        # 第一个加入的为 caller，第二个为 callee
        self.caller = None   # websocket 连接对象
        self.callee = None   # websocket 连接对象

    def is_empty(self) -> bool:
        return self.caller is None and self.callee is None

    def is_full(self) -> bool:
        return self.caller is not None and self.callee is not None

    def add_peer(self, websocket) -> bool:
        """添加一个对等端，返回是否成功"""
        if self.caller is None:
            self.caller = websocket
            logger.info(f"[Room {self.room_id}] caller 加入")
            return True
        elif self.callee is None:
            self.callee = websocket
            logger.info(f"[Room {self.room_id}] callee 加入，房间已满")
            return True
        return False

    def remove_peer(self, websocket) -> None:
        """移除一个对等端"""
        if self.caller == websocket:
            self.caller = None
            logger.info(f"[Room {self.room_id}] caller 离开")
        elif self.callee == websocket:
            self.callee = None
            logger.info(f"[Room {self.room_id}] callee 离开")

    def get_peer(self, websocket):
        """获取对方的 websocket 连接"""
        if self.caller == websocket:
            return self.callee
        elif self.callee == websocket:
            return self.caller
        return None

    def is_caller(self, websocket) -> bool:
        return self.caller == websocket


class RoomManager:
    """管理所有活跃房间"""

    def __init__(self):
        # room_id -> Room
        self._rooms: Dict[str, Room] = {}
        # websocket -> room_id
        self._peer_room: Dict[object, str] = {}

    def join_room(self, room_id: str, websocket) -> Tuple[bool, str]:
        """
        加入房间。
        返回 (success, role)，role 为 'caller' 或 'callee'
        """
        if room_id not in self._rooms:
            self._rooms[room_id] = Room(room_id)

        room = self._rooms[room_id]

        if room.is_full():
            return False, "room_full"

        success = room.add_peer(websocket)
        if success:
            self._peer_room[id(websocket)] = room_id
            role = "caller" if room.is_caller(websocket) else "callee"
            return True, role

        return False, "unknown_error"

    def leave_room(self, websocket) -> Optional[object]:
        """
        离开房间，返回对方的 websocket（如果存在）
        """
        room_id = self._peer_room.pop(id(websocket), None)
        if room_id is None:
            return None

        room = self._rooms.get(room_id)
        if room is None:
            return None

        peer = room.get_peer(websocket)
        room.remove_peer(websocket)

        # 房间为空时清理
        if room.is_empty():
            del self._rooms[room_id]
            logger.info(f"[Room {room_id}] 房间已清理")

        return peer

    def get_peer(self, websocket) -> Optional[object]:
        """获取对方的 websocket 连接"""
        room_id = self._peer_room.get(id(websocket))
        if room_id is None:
            return None
        room = self._rooms.get(room_id)
        if room is None:
            return None
        return room.get_peer(websocket)

    def get_room_id(self, websocket) -> Optional[str]:
        return self._peer_room.get(id(websocket))

    def stats(self) -> dict:
        return {
            "active_rooms": len(self._rooms),
            "connected_peers": len(self._peer_room),
        }
