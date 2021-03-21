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
            - [Version Negotiation Packet](#version-negotiation-packet)
            - [Public Reset Packet](#public-reset-packet)
            - [Regualr Packet](#regualr-packet)
        - [Frame](#frame)
            - [STREAM Frame](#stream-frame)
            - [ACK Frame](#ack-frame)
            - [STOP_WAITING Frame](#stop_waiting-frame)
            - [WINDOW_UPDATE Frame](#window_update-frame)
            - [BLOCKED Frame](#blocked-frame)
            - [CONGESTION_FEEDBACK Frame](#congestion_feedback-frame)
            - [PADDING Frame](#padding-frame)
            - [RST_STREAM Frame](#rst_stream-frame)
            - [PING Frame](#ping-frame)
            - [CONNECTION_CLOSE Frame](#connection_close-frame)
            - [GOAWAY Frame](#goaway-frame)
        - [传输参数](#传输参数-1)
        - [Error Code](#error-code)
    - [Middlebox 解析 GQUIC](#middlebox-解析-gquic)
    - [向 IETF QUIC 过渡](#向-ietf-quic-过渡)
    - [附录、参考文献](#附录参考文献)

<!-- /TOC -->

## 概述

Google QUIC 又称为 GQUIC（后面统称为 GQUIC），是由 Google 设计并进行实践的。

由于 Google QUIC 的成功，开始了 QUIC 的标准化流程，标准化的 QUIC 被称为 IETF QUIC（IQUIC）。对于 IQUIC 的细节，在 [AIOQUIC](../lib/aioquic/readme.md) 中进行了阐述。

IQUIC 和 GQUIC 之间的差异是巨大的，从协议的实现角度来看，它们是完全不同的，并且是无法相互兼容的。为了让 GQUIC 逐步向 IQUIC 靠拢和兼容，新的 GQUIC 协议开始采用和 IQUIC 类似的协议结构了（请参考 [向 IETF QUIC 过渡](#向-ietf-quic-过渡)）。

GQUIC 的特点：

- Connection establishment latency
- Flexible congestion control
- Multiplexing without head-of-line blocking
- Authenticated and encrypted header and payload
- Stream and connection flow control
- Connection migration

本文主要参考 [QUIC Wire Layout Specification](https://docs.google.com/document/d/1WJvyZflAO2pq77yOLbp9NsGjC1CHetAXV8I0fQe-B_U/edit#) 而进行的总结，该文档的版本范围适用于 Q043 及其以下版本。

对于 Q043 以上的版本，在 Google QUIC 官网中并没有详细文档，我猜想这是由于 IQUIC 开始逐步替代 GQUIC 所致。

## 连接与流

### 版本协商

### 建立连接

### 传输参数

### 断开连接

### 创建流

### 断开流

流在以下三种情况会进行关闭：

- 正常关闭，通过 STREAM Frame 中的 FIN Flag，表示该 Stream 的某个方向进行半关闭。当两个方向都进行关闭后，Stream 进行真正的关闭。
- 异常关闭，通过 RST_STREAM Frame。
- 连接关闭，当 Connection 关闭时，将隐式关闭连接中所有的 Stream。

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
|        (variable length, only regular packet)       |
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
- Connection ID，由客户端选择的一个 64 bit 随机数。连接 ID 标识了一个连接，可以在 Socket 变更时保持同一个连接（连接迁移）。
- QUIC Version，表示使用的 QUIC 版本。
- Packet Number，每个 Regular 都有 Packet Number（Special Packet 没有 PN），Endpoint 发送的第一个 Packet 的 PN 为 1，并且 PN 应该是单调递增的。

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

每个 Frame 的第一个字节都是 Type 字段，用于表明这个 Frame 的类型，在 GQUIC 中，Frame 分为以下类型：

- Special Frame

  ```txt
   +------------------+-----------------------------+
   | Type-field value |     Control Frame-type      |
   +------------------+-----------------------------+
   |     1fdooossB    |  STREAM                     |
   |     01ntllmmB    |  ACK                        |
   |     001xxxxxB    |  CONGESTION_FEEDBACK        |
   +------------------+-----------------------------+
  ```

- Regular Frame

  ```txt
  +------------------+-----------------------------+
   | Type-field value |     Control Frame-type      |
   +------------------+-----------------------------+
   | 00000000B (0x00) |  PADDING                    |
   | 00000001B (0x01) |  RST_STREAM                 |
   | 00000010B (0x02) |  CONNECTION_CLOSE           |
   | 00000011B (0x03) |  GOAWAY                     |
   | 00000100B (0x04) |  WINDOW_UPDATE              |
   | 00000101B (0x05) |  BLOCKED                    |
   | 00000110B (0x06) |  STOP_WAITING               |
   | 00000111B (0x07) |  PING                       |
   +------------------+-----------------------------+
  ```

**注意：**

- Special Frame 指的是 Type 字段中存在 Flag 标识的，这些 Flag 会决定 Frame 的一些属性。

#### STREAM Frame

STREAM 是隐式创建的，并用于传输应用层数据。

```txt
     0        1       …               SLEN
+--------+--------+--------+--------+--------+
|Type (8)| Stream ID (8, 16, 24, or 32 bits) |
|        |    (Variable length SLEN bytes)   |
+--------+--------+--------+--------+--------+

  SLEN+1  SLEN+2     …                                         SLEN+OLEN   
+--------+--------+--------+--------+--------+--------+--------+--------+
|   Offset (0, 16, 24, 32, 40, 48, 56, or 64 bits) (variable length)    |
|                    (Variable length: OLEN  bytes)                     |
+--------+--------+--------+--------+--------+--------+--------+--------+

  SLEN+OLEN+1   SLEN+OLEN+2
+-------------+-------------+
| Data length (0 or 16 bits)|
|  Optional(maybe 0 bytes)  |
+------------+--------------+
```

- Frame Type，格式为 `1fdooossB`:
  - 最高位必须为 1，表示这是个 STREAM 帧。
  - `f`， 发送端在该 Stream 的最后一个 STREAM 帧，此后发送端将不再该 Stream 上发送数据，Stream 进入了半关闭状态。
  - `d`，指示 Strema 中是否存在 Data length 字段。如果该标示为 0，意味着该 Stream 的数据直至 Packet 的结尾。
  - `ooo`，Offset 的长度，一共有 8 种长度：0, 16, 24, 32, 40, 48, 56, or 64 bit。
  - `ss`，Stream ID 的长度，一共有 4 种长度：8, 16, 24, or 32 bit。
- Stream ID，流的唯一标识。
- Offset，数据在该 Stream 的数据偏移，这也是 STREAM 接收端进行数据排序的根据。
- Data length，STREAM Frame 中的数据长度。

Stream Frame 后续紧接负载数据。

#### ACK Frame

对于接收到 Packet 后，应该发送一个新的 Packet，并包含 ACK Frame 以对收到 Packet 进行确认响应。

ACK 均是对 Packet 为单位进行响应的，并且提供了 ACK Range 的方式，对范围进行确认。

GQUIC 的 ACK 信息是不可以变更的，即一旦 ACK 了某个 Packet，即便后续该 Packet 出现在 ACK Range 的 Gap 中，也认为该 Packet 已经被 ACK 了。

ACK 往往需要和 [STOP_WAITING Frame](#stop_waiting-frame) 进行配合使用。

```txt
     0                            1  => N                     N+1 => A(aka N + 3)
+---------+-------------------------------------------------+--------+--------+
|   Type  |                   Largest Acked                 |  Largest Acked  |
|   (8)   |    (8, 16, 32, or 48 bits, determined by ll)    | Delta Time (16) |
|01nullmm |                                                 |                 |
+---------+-------------------------------------------------+--------+--------+


     A             A + 1  ==>  A + N
+--------+----------------------------------------+              
| Number |             First Ack                  |
|Blocks-1|           Block Length                 |
| (opt)  |(8, 16, 32 or 48 bits, determined by mm)|
+--------+----------------------------------------+

  A + N + 1                A + N + 2  ==>  T(aka A + 2N + 1)
+------------+-------------------------------------------------+
| Gap to next|              Ack Block Length                   |
| Block (8)  |   (8, 16, 32, or 48 bits, determined by mm)     |
| (Repeats)  |       (repeats Number Ranges times)             |
+------------+-------------------------------------------------+
     T        T+1             T+2                 (Repeated Num Timestamps)
+----------+--------+---------------------+ ...  --------+------------------+  
|   Num    | Delta  |     Time Since      |     | Delta  |       Time       |
|Timestamps|Largest |    Largest Acked    |     |Largest |  Since Previous  |
|   (8)    | Acked  |      (32 bits)      |     | Acked  |Timestamp(16 bits)|
+----------+--------+---------------------+     +--------+------------------+
```

- Frame Type: 格式为 `01ntllmmB`。
  - 最高两位 `01` 表示这是一个 ACK Frame。
  - `n`，表示该 ACK 是否有超过 1 个 ACK Range。
  - `u`，未使用。
  - `ll`，Largest Acked 的唱的。
  - `mm`，The two 'mm' bits encode the length of the Missing Packet Sequence Number Delta field as 1, 2, 4, or 6 bytes long. 
- Largest Acked: 表示接收到的最大的 Packet Number。
- Largest Acked Delta Time: Largest Acked 的 Packet Number 从接受到发送该 ACK 所经历的时间，方便接收 ACK 的一方进行 RTT 的计算。
- Ack Block Section:
  - Num Blocks: Ack Range 的数量。`n` 为 1 时存在。
  - Ack block length: Ack Range 的范围。
  - Gap to next block: ACK Range 间的 Packet 数量，这些 Packet 时没有被 ACK 的。

#### STOP_WAITING Frame

Endpoint 作为 Packet 的发送方，会等待 Peer 的 ACK，并且 Endpoint 会在本地记录 Least UNA（Least unacked number, 即最小的未 ACK 的 PN）。

而 Endpoint 可以通过 STOP_WAITING Frame 来提升 Least UNA，即不再等待某个 Packet 的 ACK 了。

这是因为如果由于丢包导致 Packet 重传，Packet Number 会用一个新的 PN，而老的就 PN 将不再使用，Endpoint 也是等待新的 PN，而不会等待老的 PN。

```txt
     0        1        2        3         4       5       6  
+--------+--------+--------+--------+--------+-------+-------+
|Type (8)|   Least unacked delta (8, 16, 32, or 48 bits)     |
|        |                       (variable length)           |
+--------+--------+--------+--------+--------+--------+------+
```

- Frame Type: 指定这是一个 STOP_WAITING Frame（00000110B 0x06）。
- Least Unacked Delta: 长度可变的包号增量，其长度与 Packet Header 中的 PN 长度一致。

```c
stop_wait_pn = current_pn - least_unacked_delta
```

Endpoint 发送 STOP_WAITING，将 Least UNA 提升至 stop_wait_pn。

通常而言，STOP_WATING Frame 的发送方应该设置 stop_wait_pn 为自己收到 ACK 中的 Largest Packet Number。

STOP_WAITING Frame 也应该进行定期发送：

> the peer periodically sends STOP_WAITING frames that signal the receiver to stop acking packets below a specified sequence number, raising the "least unacked" packet number at the receiver. 

#### WINDOW_UPDATE Frame

WINDOW_UPDATE Frame 用于告知对方自己接收流控窗口的增加。

当 Stream ID 为 0 时，作用于 Connection 级别的流控，当 Stream ID 非 0 时，作用于 Stream 级别的流控。

```txt
    0         1                 4        5                 12
+--------+--------+-- ... --+-------+--------+-- ... --+-------+
|Type(8) |    Stream ID (32 bits)   |  Byte offset (64 bits)   | 
+--------+--------+-- ... --+-------+--------+-- ... --+-------+
```

- Frame Type: 指定这是一个 WINDOW_UPDATE Frame（00000100B 0x04）。
- Stream ID: 指定需要进行流控的 Stream，当 Stream ID 为 0 则是对 Connection 的流控。
- Byte offset: 指示流控可以发送的最大字节偏移。


#### BLOCKED Frame

因为会实时通过发送 WINDOW_UPDATE 帧来控制接收缓冲区大小，所以 BLOCKED 帧理论上并不会传输的频繁。BLOCKED 最大的作用是调试和监控，参考 [Flow control in QUIC](https://docs.google.com/document/d/1F2YfdDXKpy20WVKJueEf4abn_LVZHhMUMS5gX6Pgjl4/edit#)：

> BLOCKED frames have been invaluable for debugging and monitoring purposes.

在实际应用中，当接收到一个 BLOCKED Frame 时，应该简单的抛弃该 Frame。

> This is a purely informational frame, which is extremely useful for debugging purposes. A receiver of a BLOCKED frame should simply discard it (after possibly printing a helpful log message).

```txt
     0        1        2        3         4
+--------+--------+--------+--------+--------+
|Type(8) |          Stream ID (32 bits)      |  
+--------+--------+--------+--------+--------+
```

- Frame Type: 指定这是一个 BLOCKED Frame（00000101B 0x05)。
- Stream ID: 指示由于流控原因导致被阻塞的流，若 Stream ID 为 0，表示是因为连接的流控限制所导致。

#### CONGESTION_FEEDBACK Frame

CONGESTION_FEEDBACK Frame 用于提供拥塞信息的反馈，该类型的帧仍属于实验性质：

> The CONGESTION_FEEDBACK frame is an experimental frame currently not used. It is intended to provide extra congestion feedback information outside the scope of the standard ack frame.

#### PADDING Frame

PADDING Frame 是填充帧，填充值为 0x00，且一直填充至 Packet 末尾。

由于 PADDING 的 Frame Type 为 0x00，因此该帧的所有数据均为 0x00。

#### RST_STREAM Frame

通过 RST_STREAM Frame 可以将 Stream 进行异常关闭。Stream 的创建者和接收方都可以发送 RST_STREAM。

```txt
+-------+--------+-- ... ----+--------+-- ... ------+-------+-- ... ------+
|Type(8)| StreamID (32 bits) | Byte offset (64 bits)| Error code (32 bits)|
+-------+--------+-- ... ----+--------+-- ... ------+-------+-- ... ------+
```

- Frame Type: 指定这是一个 RST_STREAM Frame（00000001B 0x01）。
- Stream ID: 指定 REST 关闭的 Stream。
- Byte offset: 指示 RST 发送者在该 Stream 上发送的总数居偏移（发送的数据总量）。
- Error code: 32 bit 的 Stream 关闭原因错误码。

#### PING Frame

PING Frame 用于验证对方是否存在，PING Frame 除了 Frame Type 外不含额外数据。

PING Frame 的接收者只需要对该 PING Frame 所在的 Packet 进行 ACK 即可。

PING Frame 默认 15s 发送一次，该 Frame 除了验证对方是否存在以及连接的有效性外，还可以避免 NAT 超时。

#### CONNECTION_CLOSE Frame

CONNECTION_CLOSE Frame 用于告知连接关闭，并且会隐式关闭所有的 Stream。

```txt
     0        1             4        5        6       7       
+--------+--------+-- ... -----+--------+--------+--------+----- ...
|Type(8) | Error code (32 bits)| Reason phrase   |  Reason phrase  
|        |                     | length (16 bits)|(variable length)
+--------+--------+-- ... -----+--------+--------+--------+----- ...

- Frame Type: 指定这是一个 CONNECTION_CLOSE Frame（00000010B 0x02）。
- Error Code: 一个 32 bit 的 Code 指示关闭的原因。
- Reason Phrase Length: 连接关闭的原因详情长度。
- Reason Phrase: 连接关闭的原因详情，该字段是 Human-readable。

```

#### GOAWAY Frame

GOAWAY Frame 告知连接应停止使用，将来可能会终止。相比于关闭连接而言，GOAWAY 并不会真正的关闭连接，也不会关闭 Stream，但是连接不应该在新建 Stream。

```txt
     0        1             4      5       6       7      8
+--------+--------+-- ... -----+-------+-------+-------+------+
|Type(8) | Error code (32 bits)| Last Good Stream ID (32 bits)| ->
+--------+--------+-- ... -----+-------+-------+-------+------+

      9        10       11  
+--------+--------+--------+----- ... 
| Reason phrase   |  Reason phrase
| length (16 bits)|(variable length)
+--------+--------+--------+----- ...
```

- Frame type: 指定这是一个 GOAWAY Frame（00000011B 0x03）。
- Error Code: 一个 32 bit 的 Code 指示关闭的原因。
- Last Good Stream ID: GOAWAY Frame 发送时的最后一个 Steam ID，如果并没有 Stream，则 Stream ID 填 0。
- Reason Phrase Length: 连接关闭的原因详情长度。
- Reason Phrase: 连接关闭的原因详情，该字段是 Human-readable。


### 传输参数

QUIC 握手时会为 QUIC 协商各种连接参数：

The handshake is responsible for negotiating a variety of transport parameters for a QUIC connection.

- 必要参数：
  - SFCW - Stream 流控窗口。
  - CFCW - Connection 流控窗口。
- 可选参数：
  - SRBF - Socket 接收缓冲区大小（这是 Socket 缓冲区大小，而流控限制的是协议栈的缓冲区大小）。
  - TCID - Connection ID 截断. 如果由 Peer 发送，则表示 Peer 支持截断 Connection ID，即在 Packet 中不传递 Connection ID，仅仅通过 Socket 区分连接。这对于临时连接，不用考虑连接迁移的场景非常游泳。
  - COPT - 该字段包含客户端或服务器请求的所有连接选项。 这些通常用于实验，并且会随着时间的推移而发展。


### Error Code

列举了 [QUIC Wire Layout Specification](https://docs.google.com/document/d/1WJvyZflAO2pq77yOLbp9NsGjC1CHetAXV8I0fQe-B_U/edit#heading=h.w9dp16sr91ee) 中所描述的 QuicErrorCodes：

ERROR CODE | Description
-|-
QUIC_NO_ERROR | There was no error. This is not valid for RST_STREAM frames or CONNECTION_CLOSE frames
QUIC_STREAM_DATA_AFTER_TERMINATION | There were data frames after the a fin or reset.
QUIC_SERVER_ERROR_PROCESSING_STREAM | There was some server error which halted stream processing.
QUIC_MULTIPLE_TERMINATION_OFFSETS | The sender received two mismatching fin or reset offsets for a single stream.
QUIC_BAD_APPLICATION_PAYLOAD | The sender received bad application data.
QUIC_INVALID_PACKET_HEADER | The sender received a malformed packet header.
QUIC_INVALID_FRAME_DATA | The sender received an frame data. The more detailed error codes below are prefered where possible.
QUIC_INVALID_FEC_DATA | FEC data is malformed.
QUIC_INVALID_RST_STREAM_DATA | Stream rst data is malformed
QUIC_INVALID_CONNECTION_CLOSE_DATA | Connection close data is malformed.
QUIC_INVALID_ACK_DATA | Ack data is malformed.
QUIC_DECRYPTION_FAILURE | There was an error decrypting.
QUIC_ENCRYPTION_FAILURE | There was an error encrypting.
QUIC_PACKET_TOO_LARGE | The packet exceeded MaxPacketSize.
QUIC_PACKET_FOR_NONEXISTENT_STREAM | Data was sent for a stream which did not exist.
QUIC_CLIENT_GOING_AWAY | The client is going away (browser close, etc.)
QUIC_SERVER_GOING_AWAY | The server is going away (restart etc.)
QUIC_INVALID_STREAM_ID | A stream ID was invalid.
QUIC_TOO_MANY_OPEN_STREAMS | Too many streams already open.
QUIC_CONNECTION_TIMED_OUT | We hit our pre-negotiated (or default) timeout
QUIC_CRYPTO_TAGS_OUT_OF_ORDER | Handshake message contained out of order tags.
QUIC_CRYPTO_TOO_MANY_ENTRIES | Handshake message contained too many entries.
QUIC_CRYPTO_INVALID_VALUE_LENGTH | Handshake message contained an invalid value length.
QUIC_CRYPTO_MESSAGE_AFTER_HANDSHAKE_COMPLETE | A crypto message was received after the handshake was complete.
QUIC_INVALID_CRYPTO_MESSAGE_TYPE | A crypto message was received with an illegal message tag.
QUIC_SEQUENCE_NUMBER_LIMIT_REACHED | Transmitting an additional packet would cause a packet number to be reused.

## Middlebox 解析 GQUIC

## 向 IETF QUIC 过渡

对于 IQUIC 的细节，已经在 [AIOQUIC](../lib/aioquic/readme.md) 中进行了描述。

## 附录、参考文献

1. [QUIC, a multiplexed stream transport over UDP](https://www.chromium.org/quic)
1. [QUIC Wire Layout Specification](https://docs.google.com/document/d/1WJvyZflAO2pq77yOLbp9NsGjC1CHetAXV8I0fQe-B_U/edit?usp=sharing)
1. [Use IETF Packet Header Wire Format in Google QUIC](https://docs.google.com/document/d/1FcpCJGTDEMblAs-Bm5TYuqhHyUqeWpqrItw2vkMFsdY/edit#)
1. [Flow control in QUIC](https://docs.google.com/document/d/1F2YfdDXKpy20WVKJueEf4abn_LVZHhMUMS5gX6Pgjl4/edit#)
1. [QUIC Loss Recovery And Congestion Control](https://tools.ietf.org/id/draft-tsvwg-quic-loss-recovery-00.html)
1. [Congestion Control and Loss Recovery](https://docs.google.com/presentation/d/1T9GtMz1CvPpZtmF8g-W7j9XHZBOCp9cu1fW0sMsmpoo/edit#slide=id.gb7cc33ba7_25_74)
1. [QUIC Crypto](https://docs.google.com/document/d/1g5nIXAIkN_Y-7XJW5K45IblHd_L2f5LTaDUDwvZ5L6g/edit)
1. [Parsing QUIC Client Hellos](https://docs.google.com/document/d/1GV2j-PGl7YGFqmWbYvzu7-UNVIpFdbprtmN9tt6USG8/preview#)
