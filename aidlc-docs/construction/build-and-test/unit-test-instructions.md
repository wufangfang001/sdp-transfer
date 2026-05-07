# 单元测试说明

## RoomManager 单元测试

### 运行测试
```bash
python -c "
from room_manager import RoomManager

rm = RoomManager()

class FakeWS:
    def __init__(self, name): self.name = name

ws1, ws2, ws3 = FakeWS('A'), FakeWS('B'), FakeWS('C')

ok, role = rm.join_room('r1', ws1)
assert ok and role == 'caller'
print('PASS: caller 加入')

ok, role = rm.join_room('r1', ws2)
assert ok and role == 'callee'
print('PASS: callee 加入')

ok, _ = rm.join_room('r1', ws3)
assert not ok
print('PASS: 房间已满拒绝')

assert rm.get_peer(ws1) == ws2
assert rm.get_peer(ws2) == ws1
print('PASS: 对方查询正确')

rm.leave_room(ws1)
rm.leave_room(ws2)
assert rm.stats()['active_rooms'] == 0
print('PASS: 房间清理')

print('所有测试通过 (5/5)')
"
```

### 测试结果（已验证）
```
PASS: caller 加入
PASS: callee 加入
PASS: 房间已满拒绝
PASS: 对方查询正确
PASS: 房间清理
所有测试通过 (5/5)
```

## 模块导入测试

```bash
python -c "import config; import room_manager; import signaling_server; print('所有模块导入成功')"
```

## 证书生成测试

```bash
python generate_cert.py
# 预期输出:
# [OK] 证书已生成: cert.pem
# [OK] 私钥已生成: key.pem
```
