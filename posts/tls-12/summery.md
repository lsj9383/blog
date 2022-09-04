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
- TLS 1.3 很好，很安全，更高效，它有着 0-RTT、握手中更少的信息泄露，支持它的 Web 站点越来越多，没有理由不学习它和讨论它。仅限于个人精力，未来有时间时进行学习总结。

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
TLS 记录协议 | record | 作为单独的分层为其他子协议的通信基础。TLS 握手完成后，在该层进行数据的保护（MAC 和加密）。
握手协议 | handshake | 协商 record layer 所需要的加密参数，同时也会认证双端身份。
密码切换协议 | change_cipher_spec | 该协议发出的消息是加密通道启动的信号。换句话说，该协议是 record layer 是否对数据进行加解密的分界线。
警告协议 | alert | 传达警告或致命的信息。具有致命级别的警告消息息会导致连接立即终止。
应用数据协议 | application_data | 该协议本质上就是 TLS 上层应用数据，TLS 保护的就是这些数据。

## Record Protocol

记录协议，即 Record Protocol，它作为 TLS 中的一个单独分层为其他 TLS 子协议的传输提供一个规范，因此 Record Protocol 单独形成一个层即 Record Layer。

Record Layer 为上层数据传输提供了以下能力：

- 分段（Fragment）
- 压缩（Compress）
- 一致性
- 机要性。

如下所示：

![](assets/record-detail.drawio.png)

**注意：**

- 上图中的分段、压缩、MAC、加密的 HEAD 部分数据主要包括：
  - 上层协议的类型（例如指出是 handshake 或者是 alert）
  - TLS 协议版本
  - HEAD 后面跟着的数据长度
- 不同的 HEAD 可能不同，例如分段的 HEAD 和压缩的 HEAD 可能不同（因为压缩后，数据长度变了）。
- 有的数据保护可能没有显式的 MAC 添加，例如 AEAD 这类的加密算法，MAC 包含在加密算法中了。
- 有的数据保护中使用的加密算法可能还会添加额外的信息，例如 AES 还会添加 IV 等初始化向量数据。

### Record 安全参数

在 Record Layer 要对数据进行压缩、MAC、加密等，那以什么算法来执行，而密钥、长度等又是怎么确定的呢？

Record Layer 需要为上层提供了设置这些安全参数的接口，同时，上层需要为 Record Layer 提供这些安全参数：

安全参数 | 描述
-|-
connection end | 这个 end 是 endpoint 的含义。标识自己在此连接中被视为 “客户端” 还是 “服务器”。
master secret | 一个 48 字节的对称密钥，由 TLS 握手协议协商而得。
PRF algorithm | 指定伪随机函数算法。master secret 并不会直接用作与 MAC 和加密，而是需要从 master secret 派生出 MAC 和加密的密钥，PRF 就是指的派生算法。固定为 PRF_SHA256。
client random | 客户端提供的 32 字节随机数。用于结合 master secret 和 PRF 派生出 MAC 和加密密钥。
server random | 服务器提供的 32 字节随机数。用于结合 master secret 和 PRF 派生出 MAC 和加密密钥。
bulk encryption algorithm | 用于加密的算法。该参数包括该算法的密钥大小，密码的块大小，以及显式和隐式初始化向量（或随机数）的长度等等所有加密相关的参数（除了密钥，因为密钥是派生出来的）。
MAC algorithm | 用于消息认证的算法，包括 MAC 的所有参数（除了密钥，因为密钥是派生出来的）。
compression algorithm | 用于数据压缩的算法。该参数必须包括算法进行压缩所需的所有信息。

完整的 TLS 1.2 Record Protocol 安全参数如下所示：

```txt
struct {
    ConnectionEnd          entity;
    PRFAlgorithm           prf_algorithm;

    BulkCipherAlgorithm    bulk_cipher_algorithm;
    CipherType             cipher_type;
    uint8                  enc_key_length;
    uint8                  block_length;
    uint8                  fixed_iv_length;
    uint8                  record_iv_length;

    MACAlgorithm           mac_algorithm;
    uint8                  mac_length;
    uint8                  mac_key_length;

    CompressionMethod      compression_algorithm;

    opaque                 master_secret[48];

    opaque                 client_random[32];
    opaque                 server_random[32];
} SecurityParameters;

enum { server, client } ConnectionEnd;

enum { tls_prf_sha256 } PRFAlgorithm;

enum { null, rc4, 3des, aes } BulkCipherAlgorithm;

enum { stream, block, aead } CipherType;

enum { null, hmac_md5, hmac_sha1, hmac_sha256, hmac_sha384, hmac_sha512} MACAlgorithm;

enum { null(0), (255) } CompressionMethod;
```

**注意：**

- 上面这样的数据结构是比较容易理解的，类似于 C 语言，但并非 C 语言，而是 TLS 1.2 协议中专门定义的表述性语言。
- 这里对有些不太容易理解，或者容易误解的地方，的这里提一下：
  - `opaque` 代表不透明的二进制数据，意思是当前结构体或者层中，并不理解该数据的内部结构，只能从变量上来判断该数据的作用。
  - `opaque client_random[32];` 这个代表的是 32 字节数据。
  - `T t[32];` 这里 t 仍然代表 32 字节的数据。若假设一个 T 占 4 字节，则意味着一个 t 是 8 个连续 T 的数组，一共占 32 字节。

#### Record 密钥计算

上面提到协商出来的 master secret 不会直接用作与 MAC 和加密，而是用来派生真实密钥的，那么实际的密钥到底是怎么生成的呢？

这里做个简单的介绍，更详细的内容可以参考 [HMAC and the Pseudorandom Function](https://www.rfc-editor.org/rfc/rfc5246.html#section-5) 和 [Key Calculation](https://www.rfc-editor.org/rfc/rfc5246.html#section-6.3)：

首先，需要理解的是，PRF 可以将任何一个 secret，再加上一个 Label，派生出任意长度且完全随机的新 secret（其实就是将原 secret 给增长了，这种又叫 Expanded Secret，同时他们两者之间在统计学意义上认为是高熵的，即完全独立和无关的）：

```txt
expanded secret = PRF(origin secret, label, seed)
```

- 这里 origin secret 就是 master secret
- 这里 Label 代表用来干嘛。当然，PRF 本身并不理解用来干嘛，只是方便给不同的业务使用相同的 master secret 派生出不同且完全独立的 expanded secret。
- seed 是一个随机数种子，不同的随机数种子生成的 expanded secret 也是完全独立的。

可能有一个疑问，为什么 Label 不能作为 seed 用？其实是可以的，算法底层实现中，seed 和 label 就是拼接起来使用的。这里这是为了方便做区分：

```txt
/* P_<hash> 是 PRF 底层算法，可以不用纠结到底是怎么实现的，只是让大家知道 label 和 seed 其实对于底层算法是没有区分的 */

PRF(secret, label, seed) = P_<hash>(secret, label + seed)
```

通过 master secret 派生出一个非常长的 expanded secret，然后再把这个 expanded secret 切成不同的部分，就形成了用于 MAC、加密的密钥了：

```txt
key_block = PRF(master_secret,                            /* origin secret */
                "key expansion",                          /* label */
                server_random + client_random             /* seed */
                );

/* 将 key_block 按长度进行切割，得到 MAC 密钥、加密密钥、IV 等 */

client_write_MAC_key[mac_key_length]
server_write_MAC_key[mac_key_length]

client_write_key[enc_key_length]
server_write_key[enc_key_length]

client_write_IV[fixed_iv_length]
server_write_IV[fixed_iv_length]
```

**注意：**

- 这些 master_secret、server_random、client_random、各种 key_length 都是由 TLS 握手协商出来的，是上层来设置的安全参数。
- 上层设置安全参数后，TLS Record Layer 自己根据这些安全参数按上述算法生成出内部实际使用的密钥。

![](assets/key-cal.drawio.png)

#### 启用 Record 安全参数和安全保护

我们再设置 Record Layer 安全参数后，什么时候 Record Layer 会使用这些安全参数对数据进行保护呢？又如何触发呢？

换句话说，TLS 1.2 协议是什么时候开始进行安全传输的？

连接建立后，无论是否进行了握手，是否协商了安全参数，或者协商过程中，连接但凡使用了 TLS 1.2 协议，那么它在任意时刻都有两个内存区：

- Current，又可以细分为两个内存区：
  - Current read
  - Current write
- Pending，又可以细分为两个内存区：
  - Pending read
  - Pending write

一共四个内存区，四个内存区各有自己一套安全参数，并且这些内存区之间是独立的。它们的作用如下：

内存区 | 作用
-|-
Current read | Record Layer 的任何数据读操作，都是用 Current read 的安全参数。
Current write | Record Layer 的任何数据写操作，都是用 Current write 的安全参数。
Pending read | 握手协商的安全参数缓存在该缓冲区。
Pending write | 握手协商的安全参数缓存在该缓冲区。

这里讨论 Record Layer 的三个阶段其不同缓冲区的安全参数，以及是如何使用的：

1. **第一个阶段**，即连接建立后，握手开始前：

在该阶段，Current 和 Pending 内存中的安全参数均为空。Current 为空的安全参数意味着 Record Layer 当前不会对数据做任何压缩和保护。

![](assets/buffer-step-1.drawio.png)

2. **第二个阶段**，即握手协商安全参数过程：

在该阶段，Record Layer 会想 Pending 内存区写入安全参数。当然此时 Current 的安全参数还是为空的。

![](assets/buffer-step-2.drawio.png)

3. **第三个阶段**，握手协商安全参数完成：

在该阶段，Pending 内存区中的安全参数复制给了 Current 内存区，并且 Pending 内存区的安全参数被清零。

![](assets/buffer-step-3.drawio.png)

这里当握手协商完毕，会执行两个操作：

- Pending 内存区的安全参数会复制到 Current 内存区，并覆盖掉原 Current 内存的安全参数。
- Pending 内存区的安全会重置为无安全参数。

Pending 中协商好的安全参数复制给 Current，那么此时 Record Layer 的所有数据读写操作都变成加密的了。很明显，这其实本质上是一种双版本，或者双缓冲机制。

那什么时候认为握手协商完毕？在 TLS 1.2 协议中，Record Layer 收发 Change Cipher Spec 协议消息，就意味着协商完毕。

**注意：**

- Pending 复制给 Current 内存区并非是单个步骤的，因为其实一共又四个内存区： Current 的读写，以及 Pending 的读写。
- 发送 Change Cipher Spec，会触发 Pending write 复制给 Current write。
- 收到 Change Cipher Spec，会触发 Pending read 复制给 Current read。
- 在 TLS 1.2 协议中，更加官方的话术是称 Current write/read 和 Pending write/read 为四种连接状态，请参考 [Connection States](https://www.rfc-editor.org/rfc/rfc5246.html#section-6.1)（当然了，这些状态不是互斥的，这里指的是这些内存区的状态）：
  - Current write state
  - Current read state
  - Pending write state
  - Pending read state
- 这里仅仅认为使用内存区更直观的表述其含义，所以用的 “内存区” 这一术语。

TLS 1.2 协议中，连接状态本身的含义就是 Record Layer 的运行环境：

> A TLS connection state is the operating environment of the TLS Record Protocol.

在握手协议中，相关参数协商完成后，就会发送 Change Cipher Spec 消息，触发 Pending 到 Current 的复制：

```txt
 Client                                               Server

 ClientHello                  -------->
                                                 ServerHello
                                                 Certificate*
                                         ServerKeyExchange*
                                         CertificateRequest*
                             <--------      ServerHelloDone
 Certificate*
 ClientKeyExchange
 CertificateVerify*

+---------------------------------------------------------------------+
|                                                                     |
| [ChangeCipherSpec]                                                  |
| Finished                     -------->                              |
|                                        [ChangeCipherSpec]           |
|                             <--------            Finished           |
|                                                                     |
+---------------------------------------------------------------------+

 Application Data             <------->     Application Data
```

**注意：**

- Client 首先发送 ChangeCipherSpec，会让 Client 首先启用写的安全参数（更具体而言，是让 Client 端的 Pending write 复制到 Current write 内存区），随后 Finished 使用 Current write 的安全参数加密发送。
- Server 随后收到 ChangeCipherSpec，会让 Server 启用读的安全参数（更具体而言，是让 Server 端的 Pending read 复制到 Current read 内存区），Server 解密 Client 发送的 Finished 并验证 Finished 数据是否符合预期。
- Server 再接着发送 ChangeCipherSpec，会让 Server 启用写的安全参数（更具体而言，是让 Server 端的 Pending write 复制到 Current write 内存区），随后 Finished 使用 Current write 的安全参数加密发送。
- 最后 client 收到 ChangeCipherSpec，会让 Client 启用读安全参数（更具体而言，是让 Client 端的呢 Pending read 复制到 Current read 内存区），随后 Client 解密 Server 发送的 Finished 并验证数据是否符合预期。
- 上图安全参数协商部分的消息，会在握手协议部分做更详细的解释。

### Record 分段

Record Layer 的上层数据，在进入 Record Layer 的时候，做的第一个事情就是给数据包添加头部并分段，最终形成 `TLSPlaintext` 的如下数据结构：

```txt
struct {
    ContentType type;                         /* 指明上层协议的含义，是个枚举，有这些协议：change_cipher_spec、alert、handshake、application_data */
    ProtocolVersion version;                  /* 正在使用的协议版本。 {3, 3} 代表 TLS 版本 1.2 */
    uint16 length;                            /* 下面那个 fragment 的长度（以字节为单位），长度不得超过 2^14 */
    opaque fragment[TLSPlaintext.length];     /* 上层数据 */
} TLSPlaintext;

enum {
    change_cipher_spec(20),
    alert(21),
    handshake(22),
    application_data(23),
    (255)
} ContentType;

struct {
    uint8 major;
    uint8 minor;
} ProtocolVersion;
```

**注意：**

- 可以认为 type, version, length 是该段中传输分段的头部。
- 这里说的 ContentType 不是指的 HTTP 的 Content-Type Header，这里指的是 Record 的上层协议枚举，例如 Handshake Protocol、Alert Protocol 这种。

### Record 压缩

如果安全参数中已经确定并指定了压缩算法，则会对 `TLSPlaintext` 进行压缩，并转换成 `TLSCompressed`

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