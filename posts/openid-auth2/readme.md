# OpenID Authentication 2.0

## Overview

OpenID Auth 2.0 是一个用户身份认证协议，在互联网早期有不少平台会使用该协议做第三方登录，例如 Steam：[基于网页浏览器的 OpenID 验证](https://partner.steamgames.com/doc/features/auth#website)。

![steam](assets/steam.png)

OpenID Auth 2.0 协议规范实际上是属于过时协议，openid 基金会并不推荐大家继续使用 OpenID Auth 2.0，取而代之的是使用 [OpenID Connect](https://openid.net/connect/)。

因为工作原因，使用了 OpenID Auth 2.0，因此为这个已经过时的协议做一个简单的梳理和总结，本文主要参考 [OpenID Authentication 2.0 - Final](https://openid.net/specs/openid-authentication-2_0.html)。

### Terminology

这里是对 OpenID Auth2.0 涉及名词的解释：

Term | Description | Sample
-|-|-
Identifier | 标识符是 HTTP 或 HTTPS 的 URI |
User-Agent | 终端用户的网页浏览器 | Chrome/FireFox/IE
Relying Party(RP) | 希望认证终端用户身份的网页应用 | [饥荒网页应用](https://accounts.klei.com/login)
OpenID Provider(OP) | OpenID Auth Server，RP 使用 OP 对用户身份进行认证 | Steam Platform
OP Endpoint URL | 接受 OpenID 身份验证协议消息的 URL，该值必须是绝对的 HTTP 或 HTTPS URL |
OP Identifier | OpenID Provider 的标识符 | http://steamcommunity.com/openid
User-Supplied Identifier | | http://steamcommunity.com/openid/id/76561198268973239
Claimed Identifier | |
OP-Local Identifier | | -


### Flow

协议流程如下所示：

1. 用户通过浏览器传递 User-Supplied Identifier 到 RP，以启动 [initiates authentication](#initiation)。
1. 在对 User-Supplied Identifier 进行 [normalizing]() 后，RP 使用 [perform discovery]() 获得用于用户身份认证的 OP 端点 URL，这个 URL 可能是一个 OP Identifier。
1. （可选）RP 和 OP 之间建立关联：使用 Diffie-Hellman 密钥交换建立共享密钥。后续 OP 将使用共享密钥签名消息，RP 使用共享密钥验证消息。
1. RP 使用 OpenID 身份验证请求，将用户的浏览器重定向到 OP。
1. OP 判断用户是否能够进行 OpenID Authentication 以及用户身份真的希望这样做（OP 提供一个页面提示用户）。
1. OP 将用户的浏览器重定向回 RP，并带有被批准的断言或认证失败消息。
1. RP 校验从 OP 返回的消息，验证的方式包括：
   - 使用 RP 和 OP 建立关系时生成的共享密钥。
   - 直接向 OP 发送请求来验证。

这是一个流程时序图：

![flow](assets/flow.png)

## Data Formats

这里对 OpenID Auth2.0 的数据形式进行阐述。这是一个示例：

- Protocol Messages

  ```text
  Key     | Value
  --------+---------------------------
  mode    | error
  error   | This is an example message
  ```

- Key-Value Form encoded:

  ```text
  mode:error
  error:This is an example message
  ```

- HTTP Encoding(POST)

  ```text
  openid.mode=error&openid.error=This%20is%20an%20example%20message
  ```

### Protocol Messages

OpenID Authentication Message 是一个映射，Key 和 Value 均为纯文本，并使用完整的 Unicode 字符集，当需要对其进行编码时，**必须**使用 UTF-8 编码。

本文中，除非特别声明为 optional，否则所有的参数都是必须的。

**注意：**

- Message 不能包含同名的 Key。

### Key-Value Form Encoding

Key-Value 形式的消息是一系列行。

每行以一个 Key 开始，后跟一个冒号，以及与 Key 相关的 Value。

该行由单个换行符终止（\n）。 Key 和 Value 不得包含换行符，Key 也不得包含冒号。

### HTTP Encoding

OpenID Auth2.0 的请求消息是有特殊要求的：

- 所有 Key 都必须以 "openid." 为前缀。此前缀可防止干扰与 OpenID 身份验证消息一起传递的其他参数。
- 当消息作为 POST 发送时，OpenID 参数必须只在 POST 正文中发送和提取。
- 作为 HTTP 请求（GET 或 POST）发送的所有消息必须包含以下字段：

Parameters | Value | Description
-|-|-
openid.ns | http://specs.openid.net/auth/2.0 | 表示使用 OpenID Auth2.0 请求。
openid.mode | Specified individually for each message type. | 允许接收者知道它正在处理什么类型的消息。如果不存在，处理方应该假设请求不是一个 OpenID 消息。

这个 HTTP 请求方式适用于 User-Agent 到 OP 和 RP，也适用于 RP 到 OP。

### Integer Representations

OpenID Auth2.0 中整数也是有特殊要求的，例如：

```text
Base 10 number | btwoc string representation
---------------+----------------------------
0              | "\x00"
127            | "\x7F"
128            | "\x00\x80"
255            | "\x00\xFF"
32768          | "\x00\x80\x00"
```

## Communication Types

OpenID Auth2.0 中有以下几种通信方式：

- 直接通信，直接使用 HTTP 请求。
- 间接通信，通过重定向间接请求。

### Direct Request

直接请求必须使用 HTTP POST。

直接请求的响应由 Key-Value 组成，且 `Content-Type` 应该是：`text/plain`。

所有的消息中必须包含以下参数：

Parameters | Value | Description
-|-|-
ns | http://specs.openid.net/auth/2.0 | 表示使用 OpenID Auth2.0 请求。

若是一个失败的响应，则响应状态码为 400，且包含以下参数：

Parameters | Required | Description
-|-|-
ns | Y | http://specs.openid.net/auth/2.0，表示使用 OpenID Auth2.0 请求。
error | Y | 易读的错误消息。
contact | N | 服务器管理员的联系地址。
reference | N | 一个令牌，便于服务器管理员定位问题。

### Indirect Request

若是一个失败的响应，OP 必须将用户代理重定向到 "openid.return_to" 的 URL，并提供以下参数：

Parameters | Required | Description
-|-|-
openid.ns | Y | http://specs.openid.net/auth/2.0，表示使用 OpenID Auth2.0 请求。
openid.mode | Y | 固定为 "error"。
openid.error | Y | 易读的错误消息。
openid.contact | N | 服务器管理员的联系地址。
openid.reference | N | 一个令牌，便于服务器管理员定位问题。

openid.return_to 不存在或其值不是有效的 URL，则服务器应该向 End User 返回一个响应，指示错误并且它不能继续。
