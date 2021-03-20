# Google QUIC

<!-- TOC -->

- [Google QUIC](#google-quic)
    - [概述](#概述)
    - [连接与流](#连接与流)
        - [版本协商](#版本协商)
        - [建立连接](#建立连接)
        - [传输参数](#传输参数)
        - [断开连接](#断开连接)
        - [创建流](#创建流)
        - [断开流](#断开流)
    - [流量控制](#流量控制)
        - [Stream 流控](#stream-流控)
        - [Stream 流控更新策略](#stream-流控更新策略)
        - [Connection 流控](#connection-流控)
        - [Connection 流控更新策略](#connection-流控更新策略)
        - [RST 考虑](#rst-考虑)
        - [与 TCP 流控的差异](#与-tcp-流控的差异)
    - [拥塞控制](#拥塞控制)
    - [协议结构](#协议结构)
        - [Packet](#packet)
        - [Frame](#frame)
    - [向 IETF QUIC 过渡](#向-ietf-quic-过渡)
    - [附录、参考文献](#附录参考文献)

<!-- /TOC -->

## 概述

Google QUIC 又称为 GQUIC（后面统称为 GQUIC），是由 Google 设计并进行实践的。

由于 Google QUIC 的成功，开始了 QUIC 的标准化流程，标准化的 QUIC 被称为 IETF QUIC（IQUIC）。

IQUIC 和 GQUIC 之间的差异是巨大的，从协议的实现角度来看，它们是完全不同的，并且是无法相互兼容的。为了让 GQUIC 逐步向 IQUIC 靠拢和兼容，新的 GQUIC 协议开始采用和 IQUIC 类似的协议结构了（请参考 [向 IETF QUIC 过渡](#向-ietf-quic-过渡)）。

GQUIC 的特点：

- Connection establishment latency
- Flexible congestion control
- Multiplexing without head-of-line blocking
- Authenticated and encrypted header and payload
- Stream and connection flow control
- Connection migration

## 连接与流

### 版本协商

### 建立连接

### 传输参数

### 断开连接

### 创建流

### 断开流

## 流量控制

GQUIC 的流控有两个层面：

- Connection 的流控。
- Stream 的流控。

任何一个接收端都存在这数据的接收缓冲区，协议库对于接收缓冲区通常有两种实现：

- 不限制接收缓冲区大小（接收到的数据全部在协议栈中进行缓存）。对于这样的实现，流控可以避免应用层消费数据速度较慢时内存无限制增长。
- 限制接收缓冲区大小。流控可以避免由于接收缓冲区满时导致的丢包重传。

初始流控限制在握手时的传输参数中给出，后续如果流控限制变化，则通过 WINDOW_UPDATE 帧告知，如果 Endpoint 发送的数据会超过 Peer 的流控限制，则发送 BLOCKED 帧告知，整体流程如下图所示：

```txt
     Endpoint                                 Peer

Initial(SFCW=10,CFCW=20)   --------->
                           <---------      STREAM(len=3)
                           <---------      STREAM(len=7)
                           <---------      BLOCKED
                           <---------      BLOCKED

-consume stream data-

WINDOW_UPDATE(offset=20)   --------->
                           <---------      STREAM(len=5)
```

通常来说，如果 Server 的应用层处理的很快，或者不构成瓶颈，可以将限制放的很大（例如 100MB）。

### Stream 流控

![](assets/fc-wnd.png)

### Stream 流控更新策略

每次在应用层消费接收缓冲区数据时，应该判断 Stream 流控窗口是否应该更新，更新条件如下：

```c
bool send_update = (flow_control_receive_offset - consumed_bytes) < (max_receive_window / 2);
```

即消费缓冲区时，如果接收缓冲区过小（小于流控限制的一半），则需要发送 WINDOW_UPDATE 帧更新对流控限制。新的限制如下所示：

```c
new_max_receive_window = (consumed_bytes + max_receive_window)
```

对于更加自动和只能的流控更新策略，涉及到了窗口的动态变化，细节可以参考 [Flow control in QUIC](https://docs.google.com/document/d/1F2YfdDXKpy20WVKJueEf4abn_LVZHhMUMS5gX6Pgjl4/edit#heading=h.hcm2y5x4qmqt) 中最后一节：Auto-tuning max receive window。

### Connection 流控

Connection 流控是将 Connection 中的所有 Stream 进行聚合考虑的：

- Connectoin 已接收的字节数是所有 Stream 已接收字节数的和。
- Connection 已消耗的字节数是所有 Stream 已消耗字节数的和。

![](assets/fc-wnd-cn.png)

上图进行 Stream 聚合后如下图所示：

![](assets/fc-wnd-cn-ag.png)

### Connection 流控更新策略

在消费数据时判断是否满足更新流控限制的条件，若满足则进行更新。更新策略和 Stream 是一致的，只是会将 Connection 中的所有 Stream 进行聚合来判断。

### RST 考虑

这一切都看着很好，但是当遇到 RST 当极端情况时我们应该小心。正如 [断开连接](#断开连接) 中提到的，当 Endpoint 接收到了 STREAM_RST 后，Stream 被重置，需要完全忽略该流上未来的数据，这就意味着：

- Peer 在发送 X 字节后发送了 RST，而 Endpoint 在接收 Y 字节后就收到了 RST，其中 Y <= X（因为 RST 可能先抵达 Endpoint），而 Endpoint 忽略了 Y 字节后的部分（X - Y）。如此，Endpoint 的连接认为我接收到了 +Y 字节，而 Peer 认为对端收到了 +X 字节，导致两端对数据量认知不一致。如下图所示

  ```txt
       Endpoint                             Peer

                        <---------      STREAM(len=3)
                        <----x----      STREAM(len=7)
                        <---------      RST_STREAM

  (认为自己接收了 3 个字节)            (认为 Endpint 接收了 10 个字节)
  ```

- Endpint 在发送 A 字节后接收到了 RST，之前发送的 A 字节不会进行任何缓存和丢包重传了，Peer 接收到了 B 字节，其中 A - B 字节由于丢包导致丢失。如此，Endpoint 认为连接发送了 +A 字节，而 Peer 认为连接上收到了 +B 字节。

  ```txt
       Endpoint                            Peer

    STREAM(len=3)       --------->
    STREAM(len=7)       -----x--->
                        <---------      RST_STREAM
  (认为自己发送了 10 个字节)           (认为自己接收了 3 个字节)
  ```

对于第一个问题，通过在 STREAM_RST 中告知已发送的字节数（即 X），来告诉 Endpoint 对端在发送 RST 前发送了多少数据。

对于第二个问题，Endpoint 在收到 RST 后需要向对端回一个 FIN 或者 RST 告知 Peer 自己发送了多少字节。

> Therefore the protocol requires that on stream termination each endpoint must send either a RST or a data frame with FIN.

### 与 TCP 流控的差异

TCP 和 GQUIC 的流控的目的其实都是一样的：

- 控制数据的发送速率，以适配接收端的数据消费速率，尽可能的内存溢出或数据丢包的问题。

但是它们之间是存在差异的：

- TCP
  - 发送的是接收缓冲区的窗口大小，本质就是接收缓冲区大小。
  - Endpoint 发送的每个 Segment 中都会带上接收 Endpoint 的接收缓冲区大小。
- GQUIC
  - 发送的是接收数据的总大小，本质上就是 已消费数据 + 接收缓冲区大小。
  - Endpint 并不会每个 Segment 中带上接收缓冲区大小，而是在需要变更的时候才会带上接收缓冲区大小。

## 拥塞控制

## 协议结构

### Packet

GQUIC 的 Packet 指的是 UDP 报文负载，因此在 GQUIC 中，一个 UDP 报文就是传输一个 QUIC Packet（这不同于 IQUIC）。

因为 Packet 就是 UDP 的负载，因此 Packet 的大小不应导致 IP 分片。

GQUIC 的 PMTU 似乎并没有进展，这在 [QUIC Wire Layout Specification](https://docs.google.com/document/d/1WJvyZflAO2pq77yOLbp9NsGjC1CHetAXV8I0fQe-B_U/edit#) 中提及：

> Path MTU discovery is a work in progress, and the current QUIC implementation uses a 1350-byte maximum QUIC packet size for IPv6, 1370 for IPv4.  Both sizes are without IP and UDP overhead.

GQUIC Packet 有两大类：

- Special Packets，这类 Packet 不包含帧（Frame）。
  - Negotiation Packets
  - Public Reset Packets
- Regular Packets，这类 Packet 包含帧。

对于 Packet 的头部格式如下：

```txt
     0        1        2        3        4            8
+--------+--------+--------+--------+--------+---    ---+
| Public |    Connection ID (64)    ...                 | ->
|Flags(8)|      (optional)                              |
+--------+--------+--------+--------+--------+---    ---+

     9       10       11        12   
+--------+--------+--------+--------+
|      QUIC Version (32)            | ->
|         (optional)                |                           
+--------+--------+--------+--------+


    13                             ....                             44
+--------+--------+--------+--------+--------+--------+--------   ------+
|                        Diversification Nonce     ...                  | ->
|                              (optional)                               |
+--------+--------+--------+--------+--------+--------+--------   ------+


    45      46       47        48       49       50
+--------+--------+--------+--------+--------+--------+
|           Packet Number (8, 16, 32, or 48)          |
|                  (variable length)                  |
+--------+--------+--------+--------+--------+--------+
```

- Public Flags
  - 0x01 = PUBLIC_FLAG_VERSION
    - 客户端发送 Packet 时，若该标识为 1，则代表 Header 中有 QUIC Version，用以告知 Peer 自己使用的 GQUIC 版本。
    - 服务器发送 Packet 时，若该标识为 1，则代表这是版本协商包（Version Negotiation Packet）。
  - 0x02 = PUBLIC_FLAG_RESET，表示这是一个 REST Packet。
  - 0x04，表示 Header 中存在 32 个字节的 Diversification Nonce。
  - 0x08，表示有 8 字节的连接 ID，所有的 Packet 中都应设置。
  - 0x30，这两个 bit 用于表示 Packet Number 的大小。
    - 0x30，表示 Packet Number 占 6 字节。
    - 0x20，表示 Packet Number 占 4 字节。
    - 0x10，表示 Packet Number 占 2 字节。
    - 0x00，表示 Packet Number 占 1 字节。
  - 0x40，保留暂未使用。
  - 0x80，未使用，必须为 0。
- Connection ID
- QUIC Version
- Packet Number

#### Version Negotiation Packet

只会由服务器下方，Public Flags 中 PUBLIC_FLAG_VERSION (0x01) 和 连接 ID 标识 (0x08) 都会被设置为 1。随后紧跟 Connection ID 字段和版本字段。

具体格式如下：

```txt
     0        1        2        3        4        5        6        7       8
+--------+--------+--------+--------+--------+--------+--------+--------+--------+
| Public |    Connection ID (64)                                                 | ->
|Flags(8)|                                                                       |
+--------+--------+--------+--------+--------+--------+--------+--------+--------+

     9       10       11        12       13      14       15       16       17
+--------+--------+--------+--------+--------+--------+--------+--------+---...--+
|      1st QUIC version supported   |     2nd QUIC version supported    |   ...
|      by server (32)               |     by server (32)                |             
+--------+--------+--------+--------+--------+--------+--------+--------+---...--+
```

#### Public Reset Packet

Public Flags 中 PUBLIC_FLAG_RESET (0x02) 和 连接 ID 标识 (0x08) 都会被设置为 1。随后紧跟 Connection ID 字段和 rest 信息。

具体格式如下：

```txt
     0        1        2        3        4         8
+--------+--------+--------+--------+--------+--   --+
| Public |    Connection ID (64)                ...  | ->
|Flags(8)|                                           |
+--------+--------+--------+--------+--------+--   --+

     9       10       11        12       13      14       
+--------+--------+--------+--------+--------+--------+---
|      Quic Tag (32)                |  Tag value map      ... ->
|         (PRST)                    |  (variable length)                         
+--------+--------+--------+--------+--------+--------+---
```

Tag Value Map 包含以下 tag：

- RNON (public reset nonce proof) - a 64-bit unsigned integer. Mandatory.
- RSEQ (rejected packet number) - a 64-bit packet number. Mandatory.
- CADR (client address) - the observed client IP address and port number. This is currently for debugging purposes only and hence is optional.

#### Regualr Packet

Regular Packet 是经过认证和加密的，Header 部分仅验证但是未加密，在 Header 后的负载是经过 AEAD 的数据。

解析 Header 后的 AEAD 的数据后，将会得到一组明文的 Frame。

### Frame

Frame 是 Packet 中承载的有效数据，而一个 Packet 中可能会有多个 Frame，但是一个 Frame 只会在一个 Packet 中，Frame 是不允许跨 Packet 的。

#### BLOCKED

因为会实时通过发送 WINDOW_UPDATE 帧来控制接收缓冲区大小，所以 BLOCKED 帧理论上并不会传输的频繁。BLOCKED 最大的作用是调试和监控，参考 [Flow control in QUIC](https://docs.google.com/document/d/1F2YfdDXKpy20WVKJueEf4abn_LVZHhMUMS5gX6Pgjl4/edit#)：

> BLOCKED frames have been invaluable for debugging and monitoring purposes.

## 向 IETF QUIC 过渡

对于 IQUIC 的细节，已经在 [AIOQUIC](lib/aioquic/readme.md) 中进行了描述。

## 附录、参考文献

1. [QUIC, a multiplexed stream transport over UDP](https://www.chromium.org/quic)
1. [QUIC Wire Layout Specification](https://docs.google.com/document/d/1WJvyZflAO2pq77yOLbp9NsGjC1CHetAXV8I0fQe-B_U/edit?usp=sharing)
1. [Use IETF Packet Header Wire Format in Google QUIC](https://docs.google.com/document/d/1FcpCJGTDEMblAs-Bm5TYuqhHyUqeWpqrItw2vkMFsdY/edit#)
1. [Flow control in QUIC](https://docs.google.com/document/d/1F2YfdDXKpy20WVKJueEf4abn_LVZHhMUMS5gX6Pgjl4/edit#)
1. [https://tools.ietf.org/id/draft-tsvwg-quic-loss-recovery-00.html](https://tools.ietf.org/id/draft-tsvwg-quic-loss-recovery-00.html)
1. [Congestion Control and Loss Recovery](https://docs.google.com/presentation/d/1T9GtMz1CvPpZtmF8g-W7j9XHZBOCp9cu1fW0sMsmpoo/edit#slide=id.gb7cc33ba7_25_74)
1. [QUIC Crypto](https://docs.google.com/document/d/1g5nIXAIkN_Y-7XJW5K45IblHd_L2f5LTaDUDwvZ5L6g/edit)
1. [Parsing QUIC Client Hellos](https://docs.google.com/document/d/1GV2j-PGl7YGFqmWbYvzu7-UNVIpFdbprtmN9tt6USG8/preview#)
