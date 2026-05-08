# 集成测试指令

## 目的

测试 WHIP 服务与外部客户端的集成。

## 测试场景

### 场景 1: WHIP POST 创建会话

**描述**: 测试通过 HTTP POST 创建 WHIP 会话

**前置条件**:
- 服务已启动: `python signaling_server.py`
- WHIP HTTP 服务监听 8080 端口

**测试步骤**:

```bash
# 准备 SDP Offer 文件
cat > offer.sdp << 'EOF'
v=0
o=- 123456789 2 IN IP4 127.0.0.1
s=Test Session
t=0 0
m=audio 0 RTP/AVP 0
a=sendonly
EOF

# 发送 POST 请求
curl -v -X POST http://localhost:8080/whip/ \
  -H "Content-Type: application/sdp" \
  --data-binary @offer.sdp
```

**预期结果**:
- HTTP 状态码: 201 Created
- 响应头包含 `Location: http://localhost:8080/whip/{resource-id}`
- 响应体包含 SDP Answer
- 响应头 `Content-Type: application/sdp`

---

### 场景 2: WHIP DELETE 终止会话

**描述**: 测试通过 HTTP DELETE 终止 WHIP 会话

**前置条件**:
- 已创建 WHIP 会话，获得 resource-id

**测试步骤**:

```bash
# 使用场景 1 返回的 resource-id
curl -v -X DELETE http://localhost:8080/whip/{resource-id}
```

**预期结果**:
- HTTP 状态码: 200 OK
- 响应体: "Resource deleted"

---

### 场景 3: DELETE 不存在的资源

**描述**: 测试删除不存在的 WHIP 资源

**测试步骤**:

```bash
curl -v -X DELETE http://localhost:8080/whip/nonexistent-id
```

**预期结果**:
- HTTP 状态码: 404 Not Found

---

### 场景 4: POST 无效 Content-Type

**描述**: 测试发送错误的 Content-Type

**测试步骤**:

```bash
curl -v -X POST http://localhost:8080/whip/ \
  -H "Content-Type: text/plain" \
  --data-binary @offer.sdp
```

**预期结果**:
- HTTP 状态码: 400 Bad Request

---

### 场景 5: POST 无效 SDP

**描述**: 测试发送无效的 SDP 内容

**测试步骤**:

```bash
echo "invalid sdp" > invalid.sdp
curl -v -X POST http://localhost:8080/whip/ \
  -H "Content-Type: application/sdp" \
  --data-binary @invalid.sdp
```

**预期结果**:
- HTTP 状态码: 400 Bad Request

---

### 场景 6: CORS 预检请求

**描述**: 测试 OPTIONS 预检请求

**测试步骤**:

```bash
curl -v -X OPTIONS http://localhost:8080/whip/ \
  -H "Origin: http://example.com" \
  -H "Access-Control-Request-Method: POST"
```

**预期结果**:
- HTTP 状态码: 200 OK
- 响应头包含 `Access-Control-Allow-Origin: *`

---

### 场景 7: HTTPS WHIP 服务

**描述**: 测试 HTTPS WHIP 服务

**前置条件**:
- SSL 证书存在
- WHIP HTTPS 服务监听 8443 端口

**测试步骤**:

```bash
curl -v -k -X POST https://localhost:8443/whip/ \
  -H "Content-Type: application/sdp" \
  --data-binary @offer.sdp
```

**预期结果**:
- HTTP 状态码: 201 Created

---

## 自动化测试脚本

```bash
#!/bin/bash
# test_whip_integration.sh

BASE_URL="http://localhost:8080"
OFFER_FILE="offer.sdp"

echo "=== WHIP 集成测试 ==="

# 测试 1: 创建会话
echo -e "\n[测试 1] POST /whip/ - 创建会话"
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST $BASE_URL/whip/ \
  -H "Content-Type: application/sdp" \
  --data-binary @$OFFER_FILE)

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n -1)

if [ "$HTTP_CODE" == "201" ]; then
    echo "✅ 通过 - 状态码: $HTTP_CODE"
else
    echo "❌ 失败 - 状态码: $HTTP_CODE"
fi

# 提取 resource-id
LOCATION=$(curl -s -I -X POST $BASE_URL/whip/ \
  -H "Content-Type: application/sdp" \
  --data-binary @$OFFER_FILE | grep -i "location:" | tr -d '\r')

RESOURCE_ID=$(echo $LOCATION | sed 's/.*\/whip\///')
echo "Resource ID: $RESOURCE_ID"

# 测试 2: 删除会话
echo -e "\n[测试 2] DELETE /whip/$RESOURCE_ID - 删除会话"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE $BASE_URL/whip/$RESOURCE_ID)

if [ "$HTTP_CODE" == "200" ]; then
    echo "✅ 通过 - 状态码: $HTTP_CODE"
else
    echo "❌ 失败 - 状态码: $HTTP_CODE"
fi

# 测试 3: 删除不存在的资源
echo -e "\n[测试 3] DELETE /whip/nonexistent - 删除不存在的资源"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X DELETE $BASE_URL/whip/nonexistent)

if [ "$HTTP_CODE" == "404" ]; then
    echo "✅ 通过 - 状态码: $HTTP_CODE"
else
    echo "❌ 失败 - 状态码: $HTTP_CODE"
fi

echo -e "\n=== 测试完成 ==="
```

## 清理

```bash
rm -f offer.sdp invalid.sdp
```
