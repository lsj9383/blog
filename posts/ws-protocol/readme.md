# WebSocket Protocol

<!-- TOC -->

- [WebSocket Protocol](#websocket-protocol)
    - [Overview](#overview)
    - [WebSocket URIs](#websocket-uris)
    - [Opening Handshake](#opening-handshake)
    - [Data Framing](#data-framing)
        - [Base Framing Protocol](#base-framing-protocol)
        - [Fragmentation](#fragmentation)
        - [Control Frames](#control-frames)
            - [Close Frame](#close-frame)
            - [Ping Frame](#ping-frame)
            - [Pong Frame](#pong-frame)
        - [Data Frames](#data-frames)
    - [Security Considerations](#security-considerations)
        - [Attacks On Infrastructure](#attacks-on-infrastructure)
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

在 WebSocket 协议中，使用一系列的帧（Frame）来进行数据传输。

从安全的角度出发（参考 [Attacks On Infrastructure](#attacks-on-infrastructure)），Client 应该混淆 Frame 的数据（无论是否使用 TLS 都应该混淆数据），混淆的方式是使用 Masking-key 做 Mask 操作，但是 Server 发送的 Frame 一定不能进行 Mask。具体而言：

- Client 发送 Masked Frame，Server 收到一个 Unmasked Frame，必须要关闭连接。
- Server 发送 Unmasked Frame，Client 收到一个 Masked Frame，必须要关闭连接。

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
Extension data | x bytes | ​ 除非在握手时协商过 Extension，否则 Extension data 长度为 0 bytes。
Application data | y bytes | 任意的应用数据，占用后面的剩余所有字节。

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

Base Framing Protocol 的 ABNF 表示方式（虽然有点长，但确实是比较严谨的方式）：

```abnf
    ws-frame                = frame-fin           ; 1 bit in length
                              frame-rsv1          ; 1 bit in length
                              frame-rsv2          ; 1 bit in length
                              frame-rsv3          ; 1 bit in length
                              frame-opcode        ; 4 bits in length
                              frame-masked        ; 1 bit in length
                              frame-payload-length   ; either 7, 7+16,
                                                     ; or 7+64 bits in
                                                     ; length
                              [ frame-masking-key ]  ; 32 bits in length
                              frame-payload-data     ; n*8 bits in
                                                     ; length, where
                                                     ; n >= 0

    frame-fin               = %x0 ; more frames of this message follow
                            / %x1 ; final frame of this message
                                  ; 1 bit in length

    frame-rsv1              = %x0 / %x1
                              ; 1 bit in length, MUST be 0 unless
                              ; negotiated otherwise

    frame-rsv2              = %x0 / %x1
                              ; 1 bit in length, MUST be 0 unless
                              ; negotiated otherwise

    frame-rsv3              = %x0 / %x1
                              ; 1 bit in length, MUST be 0 unless
                              ; negotiated otherwise

    frame-opcode            = frame-opcode-non-control /
                              frame-opcode-control /
                              frame-opcode-cont

    frame-opcode-cont       = %x0 ; frame continuation

    frame-opcode-non-control= %x1 ; text frame
                            / %x2 ; binary frame
                            / %x3-7 ; 4 bits in length, reserved for further non-control frames

    frame-opcode-control    = %x8 ; connection close
                            / %x9 ; ping
                            / %xA ; pong
                            / %xB-F ; reserved for further control frames 4 bits in length

    frame-masked            = %x0 ; frame is not masked, no frame-masking-key
                            / %x1 ; frame is masked, frame-masking-key present 1 bit in length

    frame-payload-length    = ( %x00-7D )
                            / ( %x7E frame-payload-length-16 )
                            / ( %x7F frame-payload-length-63 )
                            ; 7, 7+16, or 7+64 bits in length, respectively

    frame-payload-length-16 = %x0000-FFFF ; 16 bits in length

    frame-payload-length-63 = %x0000000000000000-7FFFFFFFFFFFFFFF
                            ; 64 bits in length

    frame-masking-key       = 4( %x00-FF )
                              ; present only if frame-masked is 1
                              ; 32 bits in length

    frame-payload-data      = (frame-masked-extension-data
                               frame-masked-application-data)
                            ; when frame-masked is 1
                              / (frame-unmasked-extension-data
                                frame-unmasked-application-data)
                            ; when frame-masked is 0

    frame-masked-extension-data     = *( %x00-FF )
                            ; reserved for future extensibility
                            ; n*8 bits in length, where n >= 0

    frame-masked-application-data   = *( %x00-FF )
                            ; n*8 bits in length, where n >= 0

    frame-unmasked-extension-data   = *( %x00-FF )
                            ; reserved for future extensibility
                            ; n*8 bits in length, where n >= 0

    frame-unmasked-application-data = *( %x00-FF )
                            ; n*8 bits in length, where n >= 0

```

### Fragmentation

为了允许发送一个未知大小消息，而不必缓存消息，支持对消息进行分片。如果消息无法分片，则网络中的 Endpoint 就会涉及到对整个消息进行缓存。

因为 WebSocket 支持消息分片，所以 Server 或 Proxy 都可以选择一个合理的缓存区大小，当缓存已满，将分片写进网络中。

分片的另外一个原因，是为了让连接更好的多路复用，例如一个大消息的传输耗时可能较长，期望中间穿插一些控制信息。

**注意：**

- 上述提到对消息进行分片，消息可以理解为就是一次应用层的数据发送，也可以理解为单个大数据帧。

下面是分片的规则：

- 一个没有分片的消息，由 Single Frame 进行传输，且 `fin=1 & opcode>0`。
- 一个被分片的消息，由多个 Frame 组成，首个 Frame `fin=0 & opcode>0`，中间有 0 个或多个 Frame `fin=0 & opcode=0`，最后有一个 Frame `fin=1 & opcode=0`
  - 分片消息帧，等价于是单个大消息帧，分片消息的所有 Payload Data 串联起来才是真正的消息数据。
- 控制帧不能进行分片，并且控制帧可能穿插在分片的数据帧中。
- 分片必须顺序的传递，因为分片没有序号信息，使用 TCP 顺序传递分片，可以对此保证。
- 多个消息的分片不能彼此交织传输，因为分片没有标识属于什么消息，因此当前消息分片传完后，才会传递下一个分片的。
- Endpoint 必须可以处理消息分片中夹杂的控制帧。
- 发送端可以发送任意大小的消息。
- Client 和 Server 必须支持分片和未分片消息的处理。

从以上规则中可以看出，消息的所有的分片帧均是属于同一个类型，并由第一个帧的 opcode 声明。

这是一些消息分片的示例：

```text
没有分片的 text 数据帧:
+----------------------+
|       Frame 1        |
+----------------------+
|  fin = 1, opcode = 1 |
+----------------------+

没有分片的 binary 数据帧:
+----------------------+
|       Frame 1        |
+----------------------+
|  fin = 1, opcode = 2 |
+----------------------+

分片的 binary 数据帧:
+----------------------+----------------------+----------------------+
|       Frame 1        |       Frame 2        |       Frame 3        |
+----------------------+----------------------+----------------------+
|  fin = 0, opcode = 2 |  fin = 0, opcode = 0 |  fin = 1, opcode = 0 |
+----------------------+----------------------+----------------------+

中间穿插控制帧的 text 数据帧：
+----------------------+----------------------+----------------------+----------------------+
|       Frame 1        |       Frame 2        |       Frame 3        |       Frame 4        |
+----------------------+----------------------+----------------------+----------------------+
|  fin = 0, opcode = 2 |  fin = 0, opcode = 0 |  fin = x, opcode = 9 |  fin = 1, opcode = 0 |
+----------------------+----------------------+----------------------+----------------------+

Frame 3 中的 fin = x，以为着 fin 是什么不重要，框架（例如 tconnd）收到控制帧，就认为是一个单独的帧，不会参与数据重组。
```

### Control Frames

控制帧通过 opcode 进行标识，包括：

- 0x8 关闭
- 0x9 Ping
- 0xA Pong

opcode 的 0xB - 0xF 是为扩展控制帧类型而保留的范围。

所有控制帧的 Payload data 长度必须为 125，并且不得分段。控制帧可以穿插在数据帧分片中。

#### Close Frame

Close 帧包含 Application Data，用于标识连接关闭的原因。如果存在 Application Data，其组成是：

- 前两个字节是 unsigned char 的状态码。
- 随后是 UTF-8 编码的连接关闭原因。

**注意：**

- Endpoint 发送 Close Frame 后，不得再发送任何数据帧。
- Endpoint 收到 Close Frame 后，Endpoint 必须要响应一个 Close Frame（状态码和请求 Close Frame 的保持一致）。
- Endpoint 可以滞后发送 Close Frame 直到当前的数据帧被发送完。
- Endpoint 收到 Close Frame 后，如果继续发送数据，不保证对端会对数据进行处理。

当 Endpoint 发送并接收到 Close Frame 后，认为 WebSocket 已经断开连接，可以进行 TCP 连接的关闭了。

#### Ping Frame

Ping 帧的目的有两个：

- keepalive，保持连接活跃。
- 检查对端是否存活。

当一个 Endpoint 发送了 Ping 帧后，对端一定要通过 Pong 帧进行响应，并且应该尽可能快的响应。

在连接建立后，任何一个端点在任意时刻，都可能发 Ping 帧，Ping 帧也可能带有 Payload Data 数据，且 Pong 帧应该将数据原样返回。

Ping 帧通常不需要应用层关心，而且大部分浏览器都不会去发 Ping 帧，也没有暴露 Ping 帧发送接口给 Javascript 使用。关于这一点，请参考 StackOverflow 上的讨论：[Sending websocket ping/pong frame from browser](https://stackoverflow.com/questions/10585355/sending-websocket-ping-pong-frame-from-browser)。

很多 WebSocket 框架（例如 engin.io），会自己定义 Ping/Pong 协议，并且这些由框架定义的 Ping/Pong 是通过数据帧来传输。

#### Pong Frame

Pong 帧的目的由两个：

- 被动发送，响应 Ping 帧。
- 主动发送，keepalive，不要求对端响应。

其中，Pong 帧主要用于对 Ping 帧的响应，且应该具有和 Ping 帧相同的 Payload Data（其实就是类似于 Echo）。

如果 Endpoint 在响应 Pong 前收到了多个 Ping，则 Endpoint 可以只处理收到的最后一个 Ping。

### Data Frames

## Security Considerations

### Attacks On Infrastructure

## References

1. [The WebSocket Protocol](https://www.rfc-editor.org/rfc/rfc6455.html)
1. [WebSocket 协议 RFC 文档（全中文翻译）](https://juejin.cn/post/6844903779192569869)
