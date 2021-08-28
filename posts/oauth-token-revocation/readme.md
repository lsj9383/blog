# OAuth 2.0 Token Revocation

## Overview

本文主要是 OAuth2.0 的一个补充：如何撤销 OAuth2.0 颁发的令牌。

主要参考文档：[OAuth 2.0 Token Revocation](https://datatracker.ietf.org/doc/html/rfc7009)。

## Token Revocation

当我们决定实现令牌撤销时：

- **一定**要支持刷新令牌的撤销
- 对于访问令牌的撤销并非必须实现，但是建议支持。

Client 向 Token Revocation Endpoint 发送 HTTPS POST 的令牌撤销请求。

同时，Client 必须要求撤销请求 URL 属于 HTTPS，因为令牌会在网络中传输。

### Revocation Request

Client 通过 `application/x-www-form-urlencoded` 参数形式构造 HTTP Body，并且有以下参数：

Parameters | Required | Description
-|:-:|-
token | Y | The token that the client wants to get revoked.
token_type_hint | N | 指定撤销的令牌类型，方便 Server 进行检索。若 Server 实现自动检测令牌类型时，可以忽略该参数。取值包括: `access_token` 和 `refresh_token`。

同时，请求中需要包含 Client Credentials 以表明第三方应用的身份。

这是一个请求示例：

```http
POST /revoke HTTP/1.1
Host: server.example.com
Content-Type: application/x-www-form-urlencoded
Authorization: Basic czZCaGRSa3F0MzpnWDFmQmF0M2JW

token=45ghiukldjahdnhzdauz&token_type_hint=refresh_token
```

Server 首先需要判断 Client 身份凭证是否有效，接着校验 Token 是否真的颁发给了该 Client，如果校验失败，Server 将返回失败信息。

接着，Server 将会把 Token 给无效化，当 Token 失效后，令牌将不能被再次使用。在实际中，这可能存在传播延时，例如一些服务器知道失效了，而另一些服务器不知道，Server 需要尽量减少这个演示。

Client 在收到 HTTP 200 的响应后，不得再使用令牌。

根据 OAuth2.0 业务自己的设计，令牌撤销时，可以考虑将关联授权的其他令牌一并撤销。通常这里有两个规则：

- 如何 Token Revocation Endpoint 支持撤销访问令牌，则撤销刷新令牌时**应该**撤销掉对应的刷新令牌。
- 当撤销访问令牌时，**可以**考虑撤销掉对应的刷新令牌。

**注意：**

- 客户端需要随时处理意外的令牌失效，这个 “意外” 的可能包括：
  - Resource Owner 主动取消了用户授权。
  - 授权服务器检测到令牌泄露，自动撤销掉令牌了。
- Resource Owner 的撤销机制并不由本文档描述。

### Revocation Response

当令牌撤销成功，OAuth2.0 Server 响应 200 HTTP 状态码。

如果 Client 本身提交的就是一个无效令牌，OAuth2.0 Server 同样返回 200 HTTP 状态码。之所以不返回错误，是考虑：

- Client 并不知道如何处理这样的错误；
- 该令牌确实已经无效了；
- 这保障该接口幂等。

OAuth2.0 Server 不会有响应 Body，即便有 Client 也应该忽略 Body，因为 HTTP 状态码中已表明了结果。

Token Revocation Endpoint 定义了一个额外的错误码：

- unsupported_token_type，不支持撤销该令牌类型。

**注意：**

- 如果服务器以 HTTP 状态代码 503 响应，则客户端必须假定令牌仍然存在，并且可以在合理的延迟后重试。
- 服务器可以在响应中包含 `Retry-After` 标头，以指示请求客户端预计该服务不可用的时间。

### Cross-Origin Support

如果 OAuth2.0 支持基于 User-Agent 的应用，那么 Token Revocation Endpoint 可以支持跨域请求。

虽然现代浏览器已经支持了 CORS 头，但是为了更好的兼容性，Token Revocation Endpoint 可以提供 JSONP 的跨域撤销。

此时，需要添加一个额外的参数：

Parameters | Required | Description
-|:-:|-
callback | N | Javascript 函数，用于 JSONP 响应时回调。

这是一个 JSONP 撤销的例子：

```http
POST /revoke?token=agabcdefddddafdd&callback=package.myCallback HTTP/1.1
Host: server.example.com
Authorization: Basic czZCaGRSa3F0MzpnWDFmQmF0M2JW
```

成功响应：

```text
package.myCallback();
```

失败响应：

```text
package.myCallback({"error":"unsupported_token_type"});
```

Client 需要意识到的是，当依赖 JSONP 时，如果 Token Revocation Endpoint 是恶意的、不安全的或者被控制了，Client 可能会被注入恶意代码。

## Implementation Note

OAuth2.0 允许使用形式各异的访问令牌：

- 访问令牌可以是自包含的，这样 Resource Endpoint 不需要和 Token Endpoint 之间有其他交互就可以判定令牌是否可以访问资源。
- 也可以使用 Handle 形式的访问令牌，因此这需要 Resource Endpoint 向 Token Endpoint 请求，以检索 Token 的内容。

**注意：**

- Handle 式令牌指的是该令牌引用了存储在 Token Endpoint 的授权数据。

## Security Considerations

若 OAuth2.0 不支持撤销访问令牌，那么刷新令牌撤销后，访问令牌将不会被立即撤销。此类实现在安全分析时，一定要考虑这一点。

使用撤销清理令牌，有助于提供整体安全和隐私，因为它减少了对废弃令牌的滥用。

恶意客户端可能会对 Token Revocation Endpoint 发起拒绝访问攻击，具体来说：错误的令牌类型将误导 Server 到额外的数据库去检索。

除此外，恶意客户端也可能会猜测有效的 Token，并调用 Revocation URL，因此我们要求客户端：

- 提供有效的 client_id （对于 Public Client）
- 提供有效的 Client 凭证（对于 Confidential Client）

不过即便是恶意客户端猜测出了有效的 Token，但因为调用了 Revocation URL，也仅仅只是导致用户授权被取消，猜测出来的令牌将变得毫无价值，因此带来的危害仅仅是让用户重新进行授权。