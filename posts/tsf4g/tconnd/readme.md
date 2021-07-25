# TSF4G Tconnd

<!-- TOC -->

- [TSF4G Tconnd](#tsf4g-tconnd)
    - [Overview](#overview)
    - [Work Mode](#work-mode)
        - [TDR Mode](#tdr-mode)
        - [QQ Mode](#qq-mode)
        - [GCP Mode](#gcp-mode)
    - [Tconnd FRAME](#tconnd-frame)
    - [Connection](#connection)
        - [Connect](#connect)
        - [Close](#close)
        - [Relay](#relay)
        - [Route](#route)
        - [Queue](#queue)
    - [Application Message](#application-message)
    - [AuthN](#authn)
    - [Event Programe](#event-programe)
    - [References](#references)

<!-- /TOC -->

## Overview

什么是 Tconnd？Tconnd 是 Tsf4g 的组件中的一部分，用作于游戏接入层，全称为 `Tencent Connection Daemon`。

Tconnd 在游戏架构中的定位下图一言以蔽之：

![system.png](assets/system.png)

Tconnd 为 Game Server 提供接入服务，使逻辑层不再关心网络层数据收发和连接管理。

## Work Mode

Tconnd 有多种工作模式（例如 TDR Mode、QQ Mode、WEB Mode），现在主流采用的是 GCP 模式，不同的工作模式区别在于使用什么通信协议以及分别方式，请参考 [Work Mode](#work-mode)。

Tconnd 支持的传输协议有：

- TCP
- UDP

Tconnd 支持的分包方式有：

分包方式 | 描述
-|-
BY_TDR | 根据 TDR 元数据分包。
BY_CHAR | 根据字符分包，遇到指定的字符就认为是一个完整的包。
BY_STR | 根据字符串分包，遇到指定的字符串就认为是一个完整的包。
BY_QQ | 根据 Tconnd 组件预定义的 TDR 元数据分包。
BY_GCP | 根据 Tconnd 组件预定义的 TDR 元数据分包。
BY_WEB | 分为两种，一种是用 http 协议进行分包；一种是基于 Tconnd 定义的 webpkg 协议分包。

这里介绍其中三个，并且 GCP Mode 是最主流的使用方式，会作为后续的主要内容。

### TDR Mode

TDR 指的是 TSF4G Data Represention，互娱研发部自研跨平台多语言数据表示组件，主要用于基于数据的序列化反序列化（支持二进制方式和 XML 文本方式）以及 ORM 数据存储。

TDR Mode 指的是通过 TDR 进行数据分包，并使用 TCP 协议进行数据透传。此时，Tconnd Server 只是以纯粹的数据透传中间件的模式存在，通过 TDR 分包模式获取到一个完整的包后，即将报文转发给后端 SVR，不存在对连接的认证过程。

这种模式下，Game Client 使用 TCLAPI。

### QQ Mode

因为公司开发或者代理的游戏大多使用 QQ 账号进行登录，QQ Mode 实现了 QQ 登录验证，消息加解密，断线重连，跨服跳转等功能。

这种模式下，分包模式是 BY_QQ，并且 Game Client 使用 TQQAPI。

### GCP Mode

GCP 指的是 General Communication Protocol，通用通信协议，GCP Mode 即 Client 采用这种协议与 Tconnd Server 进行数据交换。

QQ Mode 的缺点之一是只能使用 uint32_t 的 QQ 号，但是这已经不适合当前的游戏环境了，微信号等其他的登录方式也逐步崛起。

GCP Mode 使用 BY_GCP 的分包模式，并继承了 QQ Mode 的绝大部分能力，在此基础上提供了自定义认证的方式，能够进行 ID 映射等。

Tconnd 在 GCP 模式中，可以在建立连接时校验 Client 的用户身份，如下图所示：

![tconnd-system](assets/tconnd-system.png)

上图中，还存在一个特殊的 APS(AuthProxy Servic)，Tconnd 通过 TCP 协议将 Client 凭证传递给 APS，由 APS 对凭证进行校验。

除此外，Tconnd GCP 也具有加密通信的能力：通过 DH 协商机制，消息加密，消息压缩​。

## Tconnd FRAME

Tconnd Server 和 Game Client/Server 之间的通信方式：

- Game Client 和 Tconnd 之间在 TCP/UDP 上，通过 TDR/QQ/GCP 等协议进行通信。
- Tconnd 和 Game Server 之间在共享内存上，通过 FRAME 协议进行通信。

![tconnd-protocol](assets/tconnd-protocol.png)

也就是说，FRAME 协议是由 Tconnd 定义，用于 Tconnd 进程与后台服务进程通信的消息格式。

frame 协议中，一个包有两部分组成：

- tframehead，协议头部
- message，应用层负载

对于协议头部，tframehead：

```cpp
struct tagtframehead {
  int8_t chVer;                   // 版本信息
  int8_t chCmd;                   // 消息命令，决定了消息 stCmdData 的格式
  int8_t chExtraType;             // 是否具有 stExtraInfo 信息
  int8_t chTimeStampType;         // 是否具有 stTimeStamp 信息
  int32_t iID;                    // 会话 ID，参考 Conneciont
  int32_t iConneIdx;              // 连接 ID，参考 Conneciont
  TFRAMEHEADDATA stExtraInfo;     // 主要包括连接 IP 信息
  TTIMESTAMPDATA stTimeStamp;     // 时间戳信息
  TFRAMECMDDATA stCmdData;        // 消息数据
};
```

tframehead 中有两个关键字段：

- chCmd，用于表示数据包的类型，决定了 `stCmdData` 中什么数据有效。
- stCmdData，是一个 union，根据不同的 chCmd，会使用其中的不结构数据：

  ```cpp
  union TFRAMECMDDATA {
    TFRAMECMDSTART stStart;
    TFRAMECMDSTOP stStop;
    TFRAMECMDINPROC stInproc;
    TFRAMECMDRELAY stRelay;
    TFRAMECMDNOTIFY stNotify;
    TFRAMECMDSETROUTING stSetRouting;
    TFRAMECMDSETROUTINGRSP stSetRoutingRsp;
    TFRAMECMDSETCONNLIMIT stSetConnLimit;
    TFRAMECMDSETCONNLIMITRSP stSetConnLimitRsp;
    TFRAMECMDEXGVER stExgVer;
    TFRAMECMDWAITNUMRSP stWaitNumRsp;
    TFRAMECMDSETWAITCTR stSetWaitCtr;
  };
  ```

对于应用层负载 message 而言：

- stCmdData 并不包含应用层负载，其仍然是属于头部信息
- 应用层负载紧跟 framehead 后，解包 framehead 数据后，包剩余的数据即应用层负载。

```cpp
int data_size;
char data[1024];
// 接收底层数据
tbus_recv(tbus_handle, TBUS_ADDR_ALL, tbus_addr, data, &data_size, 0);

// 解析出 tframehead
TFRAMEHEAD *tframe_head = nullptr;
int tframe_head_size = 0;
tconnapi_decode(data, data_size, &tframe_head, &tframe_head_size);

// 解析出应用层负载
int messag_size = data_size - tframe_head_size;
std::string message(data + tframe_head_size, messag_size);
```

## Connection

Tconnd 进程使用连接池管理底层网络连接，每当 Game Client 和 Tconnd 建立一个新的连接，Tconnd Server 都会为其分配一个连接 ID，即 iConnIdx。

Tconnd Server 向 Game Server 通知连接建立消息时（即 START 消息），会通过 tframehead 传递连接 ID：iConnIdx。

Game Server 中，一个连接通常对应了一个会话，需要在响应 START 消息时，通过 tframehead 传递会话 ID：iID。

在 Tconnd 中，分为两种连接，长连接和短连接，这个长短并非针对于 TCP 连接而言，而是针对于 Tconnd 而言，也就是说 TCP 连接始终是长连接。Game Server 在响应 START 消息时，需要指出使用长连接还是短连接：

- tframehead.iID == -1，使用短连接
- 其他情况，均为长连接。

Tconnd 长连接和短连接的区别：

区别 | 长连接 | 短连接
-|-|-
上行消息 | 仅 START 消息中携带连接的源地址。 | 均携带连接的源地址。
连接关闭或异常断开 | 发送 STOP 消息。 | 不发送 STOP 消息。
iID 校验 | 检查是否一致，如果不一致则丢弃消息。 | 不检查 iID，而是检查 tframehead.IP/PORT，如果不一致则丢弃消息。

### Connect

这里提供 Game Client 连接建立流程，以及 Game Server 如何接受一个连接。

首先看一下 TDR Mode，这是一种简单的方式，这种方式没有鉴权，而且START 消息可以携带应用层数据（无论是 START 请求或是 START 响应）：
  
![tdr-connect](assets/tdr-connect.png)

GCP Mode 是我们通常会选择的方式，在建立连接时，TConnd 会对用户身份进行鉴权，请参考 [AutnN](#authn)。

除此外，GCP Mode 下建立连接会对通信信道的加密，保证鉴权凭证，应用层数据等安全传输。这是一个基于 DH Key 交换的连接建立流程:

```mermaid
sequenceDiagram
autonumber

participant client as Game Client
participant tconnd as TConnd Server
participant aps as APS
participant server as Game Server

client ->> tconnd: SYN 明文
tconnd ->> aps: DH 交换密钥请求
aps ->> aps: 生成通信的 Key
aps -->> tconnd: DH 响应
tconnd --> client: 交换通信 Key

client ->> tconnd: 带上用户身份票据，密文
tconnd ->> aps: 票据鉴权请求
aps ->> aps: 校验票据
aps -->> tconnd: 鉴权响应

tconnd ->> aps: ID 映射请求，通常将 string 类型的用户 id 映射到 uint64
aps -->> tconnd: ID 映射响应
tconnd --> client: 鉴权返回，密文

tconnd ->> tconnd: 连接排队判断
tconnd ->> server: START 消息请求
server -->> tconnd: START 消息响应
tconnd -->> client: BINGO 密文
```

Game Client 连接建立的一个伪代码:

```cpp
int service_id = 2;
int platform = TGCP_ANDROID;
int auth_mode = TGCP_AUTH_NONE;
int encrypt_method = TGCP_ENCRYPT_METHOD_AES;
int key_making_method = TGCP_KEY_MAKING_INSVR;
int max_gamedata_len = 10240;
char* pszToken = "OezXcEiiBSKSxW0eoylIeKQ_2ms051l34J6BWkiyD....";
int timeout = 50000;  //50s

// 初始化连接的句柄
HTGCPAPI handle;
int rc = tgcpapi_create(&handle);

// 设置连接的通信方式，并初始化
rc = tgcpapi_init(handle, service_id, platform, auth_mode, encrypt_method,
                  key_making_method, max_gamedata_len);

// 设置连接的账号和凭证
TGCPACCOUNT account;
stAccount.uType = TGCP_ACCOUNT_TYPE_NONE;
stAccount.bFormat = TGCP_ACCOUNT_FORMAT_STRING;
strncpy(stAccount.stAccountValue.szID, "test account", sizeof(stAccount.stAccountValue.szID));
rc = tgcpapi_set_token(handle, pszToken, strlen(pszToken));
rc = tgcpapi_set_account(handle, &account);

// 建立连接，并等待直到超时
rc = tgcpapi_start_connection(handle, "127.0.0.1:8080", timeout);

// 连接正常，但是处于排队中
if (rc == TGCP_ERR_STAY_IN_QUEUE) {
  int iBingo = -1;
  QUEUENOTIFY stNotify;

  // 一直轮询直到成功
  while(iBingo <= 0) {
    tgcpapi_query_wait_notify(handle, &iBingo, &stNotify, timeout);
  }
}
```

除此外，也可以使用事件机制，异步建立连接，请参考 [Event Programe](#event-programe)。

### Close

连接断开有两种原因：

- 正常断开：
  - Game Client 主动断开，Game Client 主动发送 Socket Close 时会进行 Game Client 的主动断开。

    ![client-close](assets/client-close.png)

  - Game Server 主动断开，Game Server 主动发送 STOP 消息时，进行主动断开。

    ![server-close](assets/server-close.png)

  - TConnd Server 主动断开，TConnd 检查到错误时或关闭时会进行主动断开。

    ![tconnd-close](assets/tconnd-close.png)

- 异常断开，客户端异常关闭 TCP 连接导致，通常对应的是 RST。

  ![exception-close](assets/exception-close.png)

连接异常断开可以进行重连，甚至也可以配置为正常断开的情况下也能进行重连，关于连接重连的信息请参考 [Relay](#relay)。

Game Client 断开连接需要关闭 Socket，也需要释放连接句柄，伪代码：

```cpp
//close
tgcpapi_close_connection(pHandle);

//fini, 与 init 相对
tgcpapi_fini(pHandle);

//destroy, 与 create 相对，释放内存。
tgcpapi_destroy(&pHandle);
```

### Relay

通常有两种情况会使用断线重连：

- TCP 连接异常运行进行断线重连，这种方式默认就支持
- Game Client 正常连接关闭后，也能进行断线重连。要支持这种方式，需要在 TConnd Server 中配置：`EnlargeReconnScopeFlag`。

对于后者的支持，主要是为了满足移动端屏幕关闭的背景，因为移动端关闭屏幕时会自动发送连接关闭请求，为了对处理这类的重连，需要针对正常关闭也能进行重连。

如果满足上述条件的连接关闭，TConnd 不会立即关闭连接，而是等待一段时间（由 `ReconnValidSec` 决定等待时间，如果为 0 则不支持断线重连）。

在客户端，当客户端检测到连接异常断开后，可以发起断线重连请求，发起断线重连会带上 TCONND 下发的身份信息。

TConnd 在收到客户端的断线重连请求后，不会去做登录鉴权，而是直接验证身份信息是否合法，如果合法则认为连接重连成功，给后端 Game Server 发送 Relay 请求，而对于旧连接则直接释放，不再发 STOP 包。

```mermaid
sequenceDiagram
autonumber

participant client as Game Client
participant tconnd as TConnd Server
participant server as Game Server

client ->> tconnd: SYN + Relay
tconnd ->> tconnd: Relay 身份校验

tconnd ->> server: RELAY 消息，并携带旧的连接 iID
server -->> tconnd: 可以设置新的 iID，也可以复用之前的

tconnd -->> client: BINGO
```

在 GCP 模式中客户端的断线重连请求除了身份信息外，还携带了鉴权数据。

当 TConnd 发现重连校验失败后，就会走新创建连接的流程，在鉴权通过后，给 Game Server 发送 START 消息，并将 START 消息中的 RelayFlag 置为 1，以此来提示 Game Server 这是一个断线重连失败的新建连接请求，Game Server 可以根据这个字段来做相应的处理。

Game Client 的重连伪代码:

```cpp
// 设置凭证，用于重连校验失败时，使用凭着建立新连接
rc = tgcpapi_set_token(handle, token, strlen(token));

// 重连请求
rc = tgcpapi_relay_connection(handle, "127.0.0.1:8080", timeout);
```

### Route

Game Server 负责处理游戏逻辑，其高负荷的 CPU 密集型处理可能会成为瓶颈，为了方便进行水平扩容，一个 TConnd 可以挂上多个 Game Server：

![tconnd-route](assets/tconnd-route.png)

TConnd Server 的路由选择是在连接建立的时刻进行的，例如上图中，Game Client 1 建立连接时 TConnd Server 将其路由给 Game Server 1，后续在这个连接上， Game Client 1 的所有数据包都是发送给 Game Server 1。

### Queue

为了保护 Game Server，TConnd 提供了排队机制。

这个排队是针对连接建立而言的，在连接建立时，会做两个维度的限制：

1. 连接总数。通过配置 `Permit` 指定 TConnd 可以维持的总连接个数。当连接超过了这个个数，TConnd 会把连接进行排队，只有当之前有连接关闭时，才会激活排队中的连接。
1. 连接速度。通过配置 `Speed` 指定 TConnd 建立连接的速度，避免对 TConnd 瞬间带来太大压力。

## Application Message

无论什么方式，应用层消息传输方式几乎是统一的，通用方式如下图所示：

![application-message](assets/application-message.png)

从图中可以看出，对于应用层数据，会通过 INPROC 消息发送给 Game Server。

## AuthN

使用 GCP 模式可以支持以下凭证：

- QQ 票据
- Wechat 授权码
- Wechat Refresh Token（免登录）
- JWT
- 其他

## Event Programe

## References

1. TSF4G-TCONND-开发指导手册
1. TConnd TGCPAPI 手游开发指导手册
1. Apollo TCONND 接入指引