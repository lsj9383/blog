# TLS 1.2 协议

[TOC]

## 概览

为了让 HTTP 能够实现传输层面的安全，引入了 HTTPS 并在业界获得极大的成功，让 HTTPS 成为标配。

能让 HTTPS 带来安全性的是其背后的 TLS 协议：

![](assets/diff-http-https.drawio.png)

TLS 发展历程：

![tls-history](assets/tls-history.png)

我们用 Chrome 浏览器打开一个网站时，通过开发者工具可以快速了解到使用的 TLS 协议以及相关安全参数：

![connection-detail](assets/connection-detail.png)

本文主要讨论 TLS 1.2 协议，为什么不是 TLS 1.1 或 TLS 1.3 呢？主要出于以下几个原因：

- TLS 1.2 非常普遍，基本每个网站都支持。根据 [ssllabs](https://www.ssllabs.com/ssl-pulse/) 的统计，99.8% 的网站支持 TLS 1.2。
- TLS 1.1 及其更早的版本存在安全性上的不足，已经很少使用，甚至已经逐步被启用:
  - [IETF 宣布正式弃用 TLS 1.0 和 TLS 1.1](https://www.cnbeta.com/articles/tech/1106281.htm)。
  - [Deprecating TLS 1.0 and TLS 1.1(RFC 8996)](https://www.rfc-editor.org/rfc/rfc8996.html)，于 2021 年形成正式 RFC。
- TLS 1.3 很好，很安全，更高效，它有着 0-RTT、握手中更少的信息泄露，支持它的 Web 站点越来越多。没有理由不学习它和讨论它。仅限于个人精力，未来有时间时进行学习总结。

从 TLS 1.2 的起草到形成最终 [RFC 5246](https://www.rfc-editor.org/rfc/rfc5246.html)，也是一个漫长的过程：

![tls12-history](assets/tls12-history.png)

TLS 1.2 的目标：

1. 加密安全：TLS 需要能够建立两端的连接安全。
1. 互操作性：程序员能够开发利用 TLS 的应用程序，这些应用程序可以在不了解彼此代码的情况下成功交换密码参数。
1. 可扩展性：TLS 提供一个框架，必要时可以将新的加密方法纳入其中。
1. 相对效率：TLS 因包含高 CPU 的密码操作以及两端握手会降低性能。出于这个原因，TLS 协议包含了一个可选的会话缓存方案，提升效率。

TLS 1.2 协议所提供的安全层中，其实包含了多个子协议，同时子协议之间有的是并列，有的是分层：

![](assets/tls-protocol-layer.drawio.png)

子协议 | 协议标识 | 描述
-|-|-
TLS 记录协议 | record layer | 作为单独的分层为其他子协议的通信基础。TLS 握手完成后，在该层进行数据的保护（MAC 和加密）。
握手协议 | handshake | 协商 record layer 所需要的加密参数，同时也会认证双端身份。
密码切换协议 | change_cipher_spec | 该协议发出的消息是加密通道启动的信号。换句话说，该协议是 record layer 是否对数据进行加解密的分界线。
警告协议 | alert | 传达警告或致命的信息。具有致命级别的警告消息息会导致连接立即终止。
应用数据协议 | application_data | 该协议本质上就是 TLS 上层应用数据，TLS 保护的就是这些数据。

## Record Protocol

### Record 密钥参数

### Record 分片

### Record 压缩

### Record 保护

Record 的保护主要是两方面：

- 目标：数据完整性。手段：使用 MAC 对称密钥进行数字签名。
- 目标：数据机要性。手段：使用读写对称密钥进行负载加密。

## Handshake Protocol

## Change Cipher Spec Protocol

## Alert Protocol

## 附录：参考文献

1. [TLS 1.2(RFC5246)](https://www.rfc-editor.org/rfc/rfc5246.html)
1. [Transport Layer Security (TLS) Extensions: Extension Definitions(RFC 6066)](https://www.rfc-editor.org/rfc/rfc6066)
1. [HTTPS 温故知新（一） —— 开篇](https://halfrost.com/https-begin/)
1. [HTTPS 温故知新（二） —— TLS 记录层协议](https://halfrost.com/https_record_layer/)
1. [HTTPS 温故知新（三） —— 直观感受 TLS 握手流程(上)](https://halfrost.com/https_tls1-2_handshake/)
1. [HTTPS 温故知新（四） —— 直观感受 TLS 握手流程(下)](https://halfrost.com/https_tls1-3_handshake/)
1. [HTTPS 温故知新（五） —— TLS 中的密钥计算](https://halfrost.com/https-key-cipher/)
1. [HTTPS 温故知新（六） —— TLS 中的 Extensions](https://halfrost.com/https-extensions/)
1. [理解 Deffie-Hellman 密钥交换算法](http://wsfdl.com/algorithm/2016/02/04/%E7%90%86%E8%A7%A3Diffie-Hellman%E5%AF%86%E9%92%A5%E4%BA%A4%E6%8D%A2%E7%AE%97%E6%B3%95.html)
1. [ssllabs](https://www.ssllabs.com/ssl-pulse/)，一个非常不错的 TLS 安全相关统计网站。