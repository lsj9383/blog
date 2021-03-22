# Game QUIC Explore

<!-- TOC -->

- [Game QUIC 探索之路](#game-quic-探索之路)
    - [概述](#概述)
    - [现状](#现状)
        - [QUIC 标准化进程](#quic-标准化进程)
        - [游戏引擎对 QUIC 的支持](#游戏引擎对-quic-的支持)
        - [QUIC Lib](#quic-lib)
        - [QUIC 闭源生态](#quic-闭源生态)
    - [QUIC Perf](#quic-perf)
    - [附录、参考文献](#附录参考文献)

<!-- /TOC -->

## 概述

IETF QUIC（下称 IQUIC）

Google QUIC（下称 GQUIC）

## 现状

### QUIC 标准化进程

### 游戏引擎对 QUIC 的支持

受限于 QUIC 协议本身仍未标准化，各个游戏引擎并未对 QUIC 做任何支持。

这是一些相关的讨论：

- [QUIC in Unity](https://forum.unity.com/threads/quic-in-unity.793914/)

  > Is QUIC even finalized in terms of specs? I don't think we're there yet. Would be cool though.

- [Are there any game clients/engines, or server libraries/frameworks that take advantage of QUIC?](https://www.reddit.com/r/gamedev/comments/eglknu/are_there_any_game_clientsengines_or_server/)
- [Question about QUIC viability for multiplayer gaming](https://www.reddit.com/r/networking/comments/gjiohd/question_about_quic_viability_for_multiplayer/fqlainn/)

也有一些对 QUIC 在游戏中的应用持有消极看法：

- <https://news.ycombinator.com/item?id=18518336>

  > These make no sense for a game engine. If we have a sequence of player movements, lets say their X position [1, 2, 3], but we miss a packet [1, -, 3] we're fine, we only want their most recent packet. But the protocol will require acknowledgment and that packet to be resent, so it will require 8 different packets be sent, instead of 3! We don't even need the packet!

- [QUIC Network Preformance Improvements](https://www.reddit.com/r/starcitizen/comments/eih33j/quic_network_preformance_improvements_dev_response/?sort=old)

  > Having quickly read through the IETF draft I don't think QUIC would be suitable for our needs because it is a stream-based protocol and provides full reliable transport of all stream data. When a connection is suffering from high packet loss, reliable stream transport can lead to head-of-line-blocking causing high latency due to the receiver needing to process all packets in the order they were sent, and any lost packets having to be re-sent before the receiver can continue processing the stream.

- [UDP for games](http://ithare.com/udp-for-games-security-encryption-and-ddos-protection/)

  > QUIC is inherently stream-oriented, and we cannot use it “as is” for fast-paced state sync stuff.

总结：

- QUIC 协议尚未完成标准化，游戏引擎并不支持 QUIC。
- 游戏领域对 QUIC 普遍不太看好，因为 QUIC 是基于流且可靠的协议，而大部分网络游戏不太依赖于协议层提供可靠性。

### QUIC Lib

市面上目前主流的 QUIC Lib 可以参考 [wiki-quic-source-code](https://en.wikipedia.org/wiki/QUIC#Source_code)。

以下是各个 QUIC 截止目前 (2021 年 3 月 23 日) 对各版本 QUIC 协议和平台的支持情况：

Lib | Language | Supported IQUIC Versions | Supported GQUIC Versions | Supported Platform | Complex
-|-|-|-|-|-
[Chromium](https://www.chromium.org/quic) | C | I27,29 | Q43,46,50 | Most | Hard
[msquic](https://github.com/microsoft/msquic) | C | I29 | - | Linux Windows | Middle
[mvfst](https://github.com/facebookincubator/mvfst) | C++ | I27 I29 | - | Linux Android iOS | Middle
[ngtcp2](https://github.com/ngtcp2/ngtcp2) | C | I22-32 | - | Linux | Middle
[quicly](https://github.com/h2o/quicly) | C | I27 | - | Most | Easy
[lsquic](https://github.com/litespeedtech/lsquic) | C | I27,29,34 | Q43,46,50 | Linux MacOS Android Windows | Middle
[picoquic](https://github.com/private-octopus/picoquic) | C | I27 | - | Linux Windows | Middle
[rawquic](https://github.com/sonysuqin/RawQuic) | C | I27,29 | Q43,46,50 | Most | Hard
[aioquic](https://github.com/aiortc/aioquic) | Python | I29,30,31,32 | - | Most | Easy
[quic-go](https://github.com/lucas-clemente/quic-go) | GO | I29,32,34  | - | Most | Unknown
[quiche](https://github.com/cloudflare/quiche) | RUST | I27,28,29  | - | Most | Unknown
`t****c` | C++ | - | Q43,46,50 | Linux Windows MacOS Android iOS | Hard
`a****a` | C++ | I27,29 | Q43,46,50 | Linux MacOS Android iOS | Hard

**注意：**

- 对于 lsquic，虽然其 [readme.md](https://github.com/litespeedtech/lsquic/blob/master/README.md) 中提到支持 Linux MacOS Android Windows 等平台，但是在 [Issues242](https://github.com/litespeedtech/lsquic/issues/242) 和 [Issues3](https://github.com/litespeedtech/lsquic/issues/3) 中其作者提到 lsquic 仅对 Linux 进行支持，其他平台并非官方提供并不做任何承诺。
- picoquic 是 QUIC 协议的极简实现，代码仍在开发中。
- quickly 提供的是纯协议栈算法，数据收发由开发人员控制，类似于 KCP，因此和环境是剥离的，但是需要开发人员写代码支持。
- 其中某些 QUIC 库是对 Chromium 的封装： rawquic, `t****c` 和 `a****a`。
- `t****c` 为 Chromium 的封装，但是没有做到对 IQUIC 的协议支持，主要原因是其需要 checkout 较老版本的 Chromium 源码，其和当前的协议存在兼容性问题。

总结：

- GQUIC 是落后的，原因有二：
  - 市面上主流 QUIC 协议栈
  - IETF QUIC 是标准，没有人愿意去实现 Google 那套。即便 Google QUIC 的 文档中也提及：
  > QUIC is now an IETF spec and its cryptographic handshake is now based on TLS 1.3 rather than this work. Thus this document is only of historical interest.
- QUIC 协议库对 IQUIC 27 和 29 的支持是最多的。
- QUIC 协议库均对 Linux 支持的较好，Chromium 对绝大多数平台支持的较好。

### QUIC 闭源生态

TEG 提供了 QUIC 接入方案：

- Server，提供 STGW 作为 QUIC 的入口和代理并通过 TCP 连接到 RS，简化 RS 开发的复杂度。
- Client，提供 `t****c` 作为开发的 SDK。

WXG 也提供了自己的 QUIC SDK：`a****a`。

STGW 支持的 QUIC 协议有：

- Q43,46,50
- I27,29,31

关系图：

优势：

- 避免重复造轮子。
- 减少服务器运维成本。
- `t****c` 支持明文模式。

劣势：

- `t****c` 对 IQUIC 的支持非常差，名义上是支持的，但是实际上建立连接会失败，这是由于 `t****c` 依赖了不兼容版本的 Chromium 所致。
- STGW 依赖了 `t****c` 进行实现，所以其对 IQUIC 的支持较差，但是其却实际上可以进行连接和通信。
- STGW 只能对 Q043 支持连接迁移。

**注意：**

- 腾讯云的 CLB 和 STGW 使用的是相同的底层技术，STGW 支持的 CLB 也会支持。
- CLB 和 STGW使用的底层技术版本可能存在不同，通常会先更新 STGW 版本，在更新 CLB 的版本。

## QUIC Perf

## 附录、参考文献

1. [wiki-quic](https://en.wikipedia.org/wiki/QUIC)
1. [IETF QUIC WG Base Draft](https://github.com/quicwg/base-drafts/wiki/Implementations)
1. [UDP for games – security (encryption and DDoS protection)](http://ithare.com/udp-for-games-security-encryption-and-ddos-protection/)
