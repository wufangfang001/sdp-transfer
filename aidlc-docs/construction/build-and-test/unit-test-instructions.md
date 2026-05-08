# 单元测试指令

## 测试框架

本项目使用 Python 内置的 `unittest` 框架。

## 测试文件

测试文件应放置在 `tests/` 目录下。

## 运行单元测试

### 1. 创建测试目录

```bash
mkdir -p tests
```

### 2. 运行所有测试

```bash
python -m pytest tests/ -v
```

或使用 unittest:

```bash
python -m unittest discover -s tests -v
```

## 测试用例

### WHIP 资源管理器测试

```python
# tests/test_whip_resource_manager.py

import unittest
import asyncio
from whip_resource_manager import WHIPResourceManager, WHIPResource

class TestWHIPResourceManager(unittest.TestCase):
    
    def setUp(self):
        self.manager = WHIPResourceManager(timeout_seconds=60)
    
    def test_create_resource(self):
        """测试资源创建"""
        sdp_offer = "v=0\no=- 123456 2 IN IP4 127.0.0.1\ns=test\nm=audio 0 RTP/AVP 0"
        resource = self.manager.create_resource(sdp_offer)
        
        self.assertIsNotNone(resource)
        self.assertIsNotNone(resource.resource_id)
        self.assertEqual(resource.sdp_offer, sdp_offer)
    
    def test_get_resource(self):
        """测试资源获取"""
        sdp_offer = "v=0\no=- 123456 2 IN IP4 127.0.0.1\ns=test\nm=audio 0 RTP/AVP 0"
        created = self.manager.create_resource(sdp_offer)
        
        retrieved = self.manager.get_resource(created.resource_id)
        self.assertEqual(created.resource_id, retrieved.resource_id)
    
    def test_delete_resource(self):
        """测试资源删除"""
        sdp_offer = "v=0\no=- 123456 2 IN IP4 127.0.0.1\ns=test\nm=audio 0 RTP/AVP 0"
        resource = self.manager.create_resource(sdp_offer)
        
        result = self.manager.delete_resource(resource.resource_id)
        self.assertTrue(result)
        
        retrieved = self.manager.get_resource(resource.resource_id)
        self.assertIsNone(retrieved)
    
    def test_delete_nonexistent_resource(self):
        """测试删除不存在的资源"""
        result = self.manager.delete_resource("nonexistent-id")
        self.assertFalse(result)
    
    def test_set_answer(self):
        """测试设置 Answer"""
        sdp_offer = "v=0\no=- 123456 2 IN IP4 127.0.0.1\ns=test\nm=audio 0 RTP/AVP 0"
        resource = self.manager.create_resource(sdp_offer)
        
        sdp_answer = "v=0\no=- 654321 2 IN IP4 127.0.0.1\ns=test\nm=audio 0 RTP/AVP 0"
        result = self.manager.set_answer(resource.resource_id, sdp_answer)
        
        self.assertTrue(result)
        self.assertEqual(resource.sdp_answer, sdp_answer)
    
    def test_stats(self):
        """测试统计信息"""
        stats = self.manager.stats()
        self.assertIn("active_resources", stats)
        self.assertIn("timeout_seconds", stats)

if __name__ == "__main__":
    unittest.main()
```

### WHIP 服务器测试

```python
# tests/test_whip_server.py

import unittest
from whip_server import WHIPServer

class TestWHIPServer(unittest.TestCase):
    
    def setUp(self):
        self.server = WHIPServer()
    
    def test_validate_sdp_valid(self):
        """测试有效的 SDP"""
        sdp = "v=0\no=- 123456 2 IN IP4 127.0.0.1\ns=test\nm=audio 0 RTP/AVP 0"
        result = self.server._validate_sdp(sdp)
        self.assertTrue(result)
    
    def test_validate_sdp_missing_field(self):
        """测试缺少必要字段的 SDP"""
        sdp = "v=0\no=- 123456 2 IN IP4 127.0.0.1"
        result = self.server._validate_sdp(sdp)
        self.assertFalse(result)
    
    def test_validate_sdp_empty(self):
        """测试空 SDP"""
        result = self.server._validate_sdp("")
        self.assertFalse(result)

if __name__ == "__main__":
    unittest.main()
```

## 预期结果

- **测试数量**: 8+
- **通过**: 全部
- **失败**: 0
- **覆盖率**: > 80%

## 故障排除

### 导入错误
确保在项目根目录运行测试，Python 能找到模块。

### 异步测试
使用 `pytest-asyncio` 插件测试异步代码:

```bash
pip install pytest-asyncio
```
