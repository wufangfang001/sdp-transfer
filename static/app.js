/**
 * WebRTC 信令客户端
 * 实现完整的 Offer/Answer/ICE Candidate 交换流程
 */

"use strict";

// ---------------------------------------------------------------------------
// 状态
// ---------------------------------------------------------------------------
let ws = null;               // WebSocket 连接
let pc = null;               // RTCPeerConnection
let localStream = null;      // 本地媒体流
let iceServers = [];         // 服务端下发的 ICE 服务器列表
let myRole = null;           // "caller" | "callee"
let isConnected = false;     // WebSocket 是否已连接

// ---------------------------------------------------------------------------
// DOM 引用
// ---------------------------------------------------------------------------
const localVideo    = document.getElementById("local-video");
const remoteVideo   = document.getElementById("remote-video");
const statusBar     = document.getElementById("status-bar");
const statusDot     = document.getElementById("status-dot");
const serverUrlInput = document.getElementById("server-url");
const roomInput     = document.getElementById("room-id");
const btnConnect    = document.getElementById("btn-connect");
const btnDisconnect = document.getElementById("btn-disconnect");
const btnCall       = document.getElementById("btn-call");
const btnHangup     = document.getElementById("btn-hangup");

// ---------------------------------------------------------------------------
// 日志 / 状态显示
// ---------------------------------------------------------------------------
function log(msg) {
  const time = new Date().toLocaleTimeString();
  statusBar.textContent = `[${time}] ${msg}`;
  console.log(`[${time}] ${msg}`);
}

function setDot(state) {
  statusDot.className = `status-dot ${state}`;
}

// ---------------------------------------------------------------------------
// WebSocket 管理
// ---------------------------------------------------------------------------
function connectServer() {
  const url = serverUrlInput.value.trim();
  const room = roomInput.value.trim();

  if (!url) { log("请输入信令服务器地址"); return; }
  if (!room) { log("请输入房间 ID"); return; }

  log(`正在连接服务器: ${url}`);
  setDot("connecting");

  ws = new WebSocket(url);

  ws.onopen = () => {
    isConnected = true;
    setDot("connected");
    log(`已连接服务器，正在加入房间: ${room}`);
    btnConnect.disabled = true;
    btnDisconnect.disabled = false;
    sendMsg({ type: "join", room });
    
    // 隐藏 WSS 提示
    document.getElementById("wss-notice").style.display = "none";
  };

  ws.onmessage = (event) => {
    let msg;
    try { msg = JSON.parse(event.data); }
    catch { log("收到无效消息"); return; }
    handleSignalingMessage(msg);
  };

  ws.onerror = (err) => {
    // 检测是否是 WSS 自签名证书问题
    if (url.startsWith("wss://")) {
      const certUrl = `https://${location.hostname || 'localhost'}:8766`;
      log(`WSS 连接失败：请先访问 ${certUrl} 信任自签名证书`);
    } else {
      log("WebSocket 错误，请检查服务器地址");
    }
    console.error(err);
  };

  ws.onclose = () => {
    isConnected = false;
    setDot("disconnected");
    if (url.startsWith("wss://")) {
      const certUrl = `https://${location.hostname || 'localhost'}:8766`;
      log(`WSS 连接断开：请先访问 ${certUrl} 信任自签名证书`);
    } else {
      log("与服务器的连接已断开");
    }
    btnConnect.disabled = false;
    btnDisconnect.disabled = true;
    btnCall.disabled = true;
    btnHangup.disabled = true;
  };
}

function disconnectServer() {
  closePeerConnection();
  if (isConnected) sendMsg({ type: "leave" });
  if (ws) { ws.close(); ws = null; }
  myRole = null;
}

function sendMsg(data) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify(data));
  }
}

// ---------------------------------------------------------------------------
// 信令消息处理
// ---------------------------------------------------------------------------
async function handleSignalingMessage(msg) {
  switch (msg.type) {

    case "joined":
      myRole = msg.role;
      iceServers = msg.iceServers || [];
      log(`已加入房间，角色: ${myRole}。等待对方加入...`);
      break;

    case "peer-joined":
      log("对方已加入房间！");
      if (myRole === "caller") {
        // caller 主动发起 Offer
        btnCall.disabled = false;
        log("您是发起方，点击「开始通话」发起呼叫");
      } else {
        log("您是接听方，等待对方发起呼叫...");
      }
      break;

    case "peer-left":
      log("对方已离开房间");
      closePeerConnection();
      break;

    case "peer-hangup":
      log("对方已挂断，可以重新发起通话");
      closePeerConnection();
      // 双方都可以重新发起通话
      if (myRole) btnCall.disabled = false;
      break;

    case "offer":
      log("收到 SDP Offer，正在处理...");
      await handleOffer(msg.sdp);
      break;

    case "answer":
      log("收到 SDP Answer，正在处理...");
      await handleAnswer(msg.sdp);
      break;

    case "ice-candidate":
      await handleRemoteIceCandidate(msg.candidate);
      break;

    case "error":
      log(`服务器错误: ${msg.message}`);
      break;

    default:
      console.warn("未知消息类型:", msg.type);
  }
}

// ---------------------------------------------------------------------------
// 媒体流
// ---------------------------------------------------------------------------
async function getLocalStream() {
  if (localStream) return localStream;
  
  // 检测是否支持 getUserMedia
  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    const isSecure = location.protocol === "https:" || location.hostname === "localhost" || location.hostname === "127.0.0.1";
    if (!isSecure) {
      throw new Error("摄像头/麦克风访问需要 HTTPS 或 localhost。请使用 https:// 访问，或配置反向代理。");
    }
    throw new Error("浏览器不支持 getUserMedia API");
  }
  
  try {
    localStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
    localVideo.srcObject = localStream;
    log("已获取本地摄像头和麦克风");
    return localStream;
  } catch (err) {
    log(`无法获取媒体设备: ${err.message}`);
    throw err;
  }
}

// ---------------------------------------------------------------------------
// RTCPeerConnection 管理
// ---------------------------------------------------------------------------
function createPeerConnection() {
  const config = { iceServers: iceServers.length ? iceServers : [{ urls: "stun:stun.l.google.com:19302" }] };
  pc = new RTCPeerConnection(config);

  // 本地 ICE Candidate 收集完成后发送给对方
  pc.onicecandidate = (event) => {
    if (event.candidate) {
      sendMsg({ type: "ice-candidate", candidate: event.candidate });
    }
  };

  pc.oniceconnectionstatechange = () => {
    log(`ICE 连接状态: ${pc.iceConnectionState}`);
    if (pc.iceConnectionState === "connected" || pc.iceConnectionState === "completed") {
      log("WebRTC 连接已建立！");
      btnHangup.disabled = false;
      btnCall.disabled = true;
    }
    if (pc.iceConnectionState === "failed" || pc.iceConnectionState === "disconnected") {
      log("WebRTC 连接中断");
    }
  };

  // 接收远端媒体流
  pc.ontrack = (event) => {
    log("收到远端媒体流");
    if (remoteVideo.srcObject !== event.streams[0]) {
      remoteVideo.srcObject = event.streams[0];
    }
  };

  return pc;
}

// ---------------------------------------------------------------------------
// RTCPeerConnection 清理（不影响房间状态）
// ---------------------------------------------------------------------------
function closePeerConnection() {
  if (pc) {
    pc.onicecandidate = null;
    pc.oniceconnectionstatechange = null;
    pc.ontrack = null;
    pc.close();
    pc = null;
  }
  if (localStream) {
    localStream.getTracks().forEach(t => t.stop());
    localStream = null;
    localVideo.srcObject = null;
  }
  remoteVideo.srcObject = null;
  btnHangup.disabled = true;
}

// ---------------------------------------------------------------------------
// 发起通话（Caller 或重新发起）
// ---------------------------------------------------------------------------
async function startCall() {
  btnCall.disabled = true;
  try {
    // 确保旧连接已清理
    closePeerConnection();
    createPeerConnection();

    // 重新获取媒体流
    const stream = await getLocalStream();
    stream.getTracks().forEach(track => pc.addTrack(track, stream));

    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);

    log("已创建 SDP Offer，发送给对方...");
    sendMsg({ type: "offer", sdp: pc.localDescription });

  } catch (err) {
    log(`发起通话失败: ${err.message}`);
    btnCall.disabled = false;
  }
}

// ---------------------------------------------------------------------------
// 处理 Offer（Callee 或重新接听）
// ---------------------------------------------------------------------------
async function handleOffer(sdp) {
  try {
    // 确保旧连接已清理
    closePeerConnection();
    createPeerConnection();

    const stream = await getLocalStream();
    stream.getTracks().forEach(track => pc.addTrack(track, stream));

    await pc.setRemoteDescription(new RTCSessionDescription(sdp));

    const answer = await pc.createAnswer();
    await pc.setLocalDescription(answer);

    log("已创建 SDP Answer，发送给对方...");
    sendMsg({ type: "answer", sdp: pc.localDescription });

  } catch (err) {
    log(`处理 Offer 失败: ${err.message}`);
  }
}

// ---------------------------------------------------------------------------
// 处理 Answer（Caller）
// ---------------------------------------------------------------------------
async function handleAnswer(sdp) {
  try {
    await pc.setRemoteDescription(new RTCSessionDescription(sdp));
    log("已设置远端 SDP Answer，等待 ICE 协商...");
  } catch (err) {
    log(`处理 Answer 失败: ${err.message}`);
  }
}

// ---------------------------------------------------------------------------
// ICE Candidate 处理
// ---------------------------------------------------------------------------
async function handleRemoteIceCandidate(candidate) {
  if (!pc) return;
  try {
    await pc.addIceCandidate(new RTCIceCandidate(candidate));
  } catch (err) {
    console.warn("添加 ICE Candidate 失败:", err);
  }
}

// ---------------------------------------------------------------------------
// 挂断
// ---------------------------------------------------------------------------
function hangup() {
  closePeerConnection();

  // 通知对方挂断（保持房间状态，不离开房间）
  if (isConnected) sendMsg({ type: "hangup" });

  // 挂断后双方都可以重新发起通话
  if (myRole) btnCall.disabled = false;

  log("通话已结束，可以重新开始通话");
}

// ---------------------------------------------------------------------------
// 按钮事件绑定
// ---------------------------------------------------------------------------
btnConnect.addEventListener("click", connectServer);
btnDisconnect.addEventListener("click", disconnectServer);
btnCall.addEventListener("click", startCall);
btnHangup.addEventListener("click", hangup);

// 检测 WSS 连接并显示提示
serverUrlInput.addEventListener("input", () => {
  const url = serverUrlInput.value.trim();
  const wssNotice = document.getElementById("wss-notice");
  if (url.startsWith("wss://")) {
    wssNotice.style.display = "block";
  } else {
    wssNotice.style.display = "none";
  }
});

// 根据页面访问地址自动填写服务器地址
(function autoFillServerUrl() {
  const protocol = location.protocol === "https:" ? "wss:" : "ws:";
  const host = location.hostname || "localhost";
  // WS 默认 8765, WSS 默认 8766
  const port = location.protocol === "https:" ? "8766" : "8765";
  serverUrlInput.value = `${protocol}//${host}:${port}`;
  
  // 更新 WSS 证书提示链接
  const wssCertLink = document.getElementById("wss-cert-link");
  if (wssCertLink) {
    wssCertLink.href = `https://${host}:8766`;
    wssCertLink.textContent = `https://${host}:8766`;
  }
})();

// 检测是否为安全上下文（非 localhost 的 HTTP 无法访问摄像头）
(function checkSecureContext() {
  const isSecure = location.protocol === "https:" || 
                   location.hostname === "localhost" || 
                   location.hostname === "127.0.0.1";
  
  if (!isSecure && (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia)) {
    // 显示警告
    const statusBar = document.getElementById("status-bar");
    statusBar.innerHTML = `<span style="color:#ef4444;">⚠️ 非 HTTPS 访问无法使用摄像头/麦克风。请使用 localhost 或配置 HTTPS。</span>`;
    // 禁用通话按钮
    document.getElementById("btn-call").disabled = true;
    document.getElementById("btn-call").title = "非 HTTPS 无法访问摄像头";
  }
})();

// 页面关闭时清理
window.addEventListener("beforeunload", () => {
  closePeerConnection();
  if (isConnected) sendMsg({ type: "leave" });
  if (ws) ws.close();
});
