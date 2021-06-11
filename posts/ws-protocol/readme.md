# WebSocket Protocol

<!-- TOC -->

- [WebSocket Protocol](#websocket-protocol)
    - [Overview](#overview)
    - [WebSocket URIs](#websocket-uris)
    - [Opening Handshake](#opening-handshake)
    - [Data Framing](#data-framing)
        - [Base Framing Protocol](#base-framing-protocol)
        - [Fragmentation](#fragmentation)
    - [References](#references)

<!-- /TOC -->

## Overview

Client 握手请求：

```http
GET /chat HTTP/1.1
Host: server.example.com
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==
Origin: http://example.com
Sec-WebSocket-Protocol: chat, superchat
Sec-WebSocket-Version: 13
```

Server 握手响应：

```http
HTTP/1.1 101 Switching Protocols
Upgrade: websocket
Connection: Upgrade
Sec-WebSocket-Accept: s3pPLMBiTxaQ9kYGzzhZRbK+xOo=
Sec-WebSocket-Protocol: chat
```

在握手成功以后，客户端和服务端传输的数据来回传输的数据单位，我们在规范中称为消息（messages）。

在传输中，一条消息有一个或者多个帧组成。

## WebSocket URIs

```text
ws-URI = "ws:" "//" host [ ":" port ] path [ "?" query ]
wss-URI = "wss:" "//" host [ ":" port ] path [ "?" query ]
```

对于端口，port 是可选的:

- "ws" 默认为 80
- "wss" 默认为 443

在 WebSocket URIs 中，Fragment 标识(#) 是没有意义的，并且禁止在 WebSocket URIs 中使用 #。

若使用 "#" 字符（不是表示 fragment），必须编码为 `%23`。

## Opening Handshake

## Data Framing

一个 WebSocket 消息可以拆分为多个数据帧。

### Base Framing Protocol

数据帧协议结构：

```text
  0                   1                   2                   3
  0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
 +-+-+-+-+-------+-+-------------+-------------------------------+
 |F|R|R|R| opcode|M| Payload len |    Extended payload length    |
 |I|S|S|S|  (4)  |A|     (7)     |             (16/64)           |
 |N|V|V|V|       |S|             |   (if payload len==126/127)   |
 | |1|2|3|       |K|             |                               |
 +-+-+-+-+-------+-+-------------+ - - - - - - - - - - - - - - - +
 |     Extended payload length continued, if payload len == 127  |
 + - - - - - - - - - - - - - - - +-------------------------------+
 |                               |Masking-key, if MASK set to 1  |
 +-------------------------------+-------------------------------+
 | Masking-key (continued)       |          Payload Data         |
 +-------------------------------- - - - - - - - - - - - - - - - +
 :                     Payload Data continued ...                :
 + - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - +
 |                     Payload Data continued ...                |
 +---------------------------------------------------------------+
```

数据帧中各部分的含义：

Field | Length | Description
-|-|-
FIN | 1 bits |  表示这是消息的最后一个片段。第一个片段也有可能是最后一个片段。
RSV1/RSV2/RSV3 | 3 bits | 必须设置为 0，除非扩展了非 0 值含义的扩展。
Opcode | 4 bits | Defines the interpretation of the "Payload data". opcode 含义请参考下一个表。
Mask | 1 bits | Mask 标志位，定义 Payload data 是否添加掩码。如果设置为1，那么 Mask Key 存在于 Masking-Key 部分。<br>All frames sent from client to server have this bit set to 1.
Payload length | 7 or 7+16 or 7+64 bits | The length of the "Payload data". <br>如果取值在 0-125 之间，则这就是 Payload data 的长度。<br>如果取值为 126，则后面两字节表示 Payload data 的长度。<br>如果取值为 127，则后面八字节表示 Payload data 的长度。
Masking-key | 0 or 32 bits | 如果 Mask 标识为 1，则 Masking-key 存在，且为 4 字节。否则 Masking-key 不存在。
Payload data | x + y bytes| Payload Data 包含两个部分：Extension data (x bytes) 和 Application data(y bytes)
Extension data | x bytes | ​ 除非协商过扩展，否则 Extension data 长度为 0 bytes。
Application data | y bytes | 任意的应用数据，占用后面的剩余所有字段。

Opcode 的含义：

Opcode | Description
-|-
​ %x0 | 表示一个持续帧。消息被分片后，后续帧都的 opcode 均使用 0，表示这是一个持续帧。
​ %x1 | 表示一个 text 帧
​ %x2 | 表示一个 binary 帧
​ %x3-7 | 预留给以后的非控制帧
​ %x8 | 表示连接关闭
​ %x9 | 表示 ping
​ %xA | 表示 pong
​ %xB-F | 预留给以后的控制帧

### Fragmentation

消息分片的原因：

- 中间代理的缓冲区是未知的，代理可以根据自己的缓冲大小将消息进行分片，以便数据过大导致代理的缓冲区撑爆。因此代理可以选择一个合理的缓存长度，当缓存区满了以后，就想网络发送一个片段。
- 消息分片使用的场景是不适合在一个逻辑通道内传输一个大的消息占满整个输出频道的多路复用场景。多路复用需要能够将消息进行自由的切割成更小的片段来共享输出频道。

消息中的所有帧，都是同一个类型的，并且该类型通过消息的第一个帧的 opcode 来进行指明。

分片中可以插入一个控制帧，如果不能插入，心跳（ping）的等待时间可能会变很长，例如在一个很大的消息之后。因此，在分片的消息传输中插入控制帧是有必要的。

## References

1. [The WebSocket Protocol](https://www.rfc-editor.org/rfc/rfc6455.html)
1. [WebSocket 协议 RFC 文档（全中文翻译）](https://juejin.cn/post/6844903779192569869)
