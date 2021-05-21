# OAuth 2.0 Security Best Current Practice

<!-- TOC -->

- [OAuth 2.0 Security Best Current Practice](#oauth-20-security-best-current-practice)
    - [Overview](#overview)
    - [Recommendations](#recommendations)
        - [Protecting Redirect-Based Flows](#protecting-redirect-based-flows)
        - [Token Replay Prevention](#token-replay-prevention)
            - [Refresh Tokens](#refresh-tokens)
        - [Access Token Privilege Restriction](#access-token-privilege-restriction)
        - [Resource Owner Password Credentials Grant](#resource-owner-password-credentials-grant)
        - [Client Authentication](#client-authentication)
        - [Other Recommendations](#other-recommendations)
    - [The Updated OAuth 2.0 Attacker Model](#the-updated-oauth-20-attacker-model)
    - [Attacks and Mitigation](#attacks-and-mitigation)
        - [Insufficient Redirect URI Validation](#insufficient-redirect-uri-validation)
        - [Credential Leakage via Referer Headers](#credential-leakage-via-referer-headers)
        - [Credential Leakage via Browser History](#credential-leakage-via-browser-history)
        - [Mix-Up Attacks](#mix-up-attacks)
        - [Authorization Code Injection](#authorization-code-injection)
        - [Access Token Injection](#access-token-injection)
        - [Cross Site Request Forgery](#cross-site-request-forgery)
        - [PKCE Downgrade Attack](#pkce-downgrade-attack)
        - [Access Token Leakage at the Resource Server](#access-token-leakage-at-the-resource-server)
        - [Open Redirection](#open-redirection)
        - [307 Redirect](#307-redirect)
        - [TLS Terminating Reverse Proxies](#tls-terminating-reverse-proxies)
        - [Refresh Token Protection](#refresh-token-protection)
        - [Client Impersonating Resource Owner](#client-impersonating-resource-owner)
        - [Click jacking](#click-jacking)
    - [References](#references)

<!-- /TOC -->

## Overview

本文主要参考 [draft-ietf-oauth-security-topics-18](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-security-topics)，并对其进行总结和梳理。

该文档会涵盖 OAuth2.0 最新的最佳安全实践。

## Recommendations

这部分是 OAuth 工作小组推荐的 OAuth 实施方式，这里面涉及到的一些攻击会在 [Attacks and Mitigation](#attacks-and-mitigation) 部分提到。

### Protecting Redirect-Based Flows

### Token Replay Prevention

授权服务器或资源服务器应该使用 sender-constraining 的 Access Token 来避免 Token 重放，例如 Mutual TLS for OAuth 2.0。

可参考 [Access Token Leakage at the Resource Server](#access-token-leakage-at-the-resource-server) 的讨论。

#### Refresh Tokens

刷新令牌防重放攻击，需要考虑对 sender-constraining 或者使用 Refresh Token 轮换的策略。

可参考 [Refresh Token Protection](#refresh-token-protection) 的讨论。

### Access Token Privilege Restriction

### Resource Owner Password Credentials Grant

### Client Authentication

Authorization servers 应该尽可能的去验证 Client 的身份。

推荐的方式是采用非对称密钥（基于公钥），例如 [mTLS](https://www.rfc-editor.org/rfc/rfc8705.html) 和 [private_key_jwt](https://openid.net/specs/openid-connect-core-1_0.html#ClientAuthentication)。

### Other Recommendations

## The Updated OAuth 2.0 Attacker Model

攻击者模型描述了可能存在的攻击者。

OAuth 必须确保 Resource Owner(RO) 在 Authorization Server(AS) 的授权，以及后续的使用 Access Token  访问 Resource Server(RS) 受到保护，以抵御以下攻击者的攻击：

Attacker | Description
-|-
A1 | Web Attackers，可以控制任意数量的网络端点（包括浏览器和服务器，RO、AS 和 RS 除外）。A1 可能会设置 RO 所访问的网站，操作用户代理以及传输协议。
A2 | Network Attackers，可以窃听、操作和欺骗网络消息，除非这些消息受 TLS 保护。A2 也可以阻止任意消息。
A3 | 能够读取，但是不能修改授权响应的攻击者。
A4 | 能够读取，但是不能修改授权请求的攻击者。
A5 | 攻击者可以获得 AS 颁发的访问令牌。

## Attacks and Mitigation

### Insufficient Redirect URI Validation

重定向 URI 验证不足。

### Credential Leakage via Referer Headers

机密信息可能会由于 Referer 头泄露给 Attacker。以下信息可能会泄露：

- code / access_token。
- state，这可能会导致 csrf 防御措施失效。

**Leakage from the OAuth Client**

作为一个成功授权请求的结果，Client 很可能会直接渲染一个页面，页面可能会：

- 包含了 Attacker 的页面连接，并且用户可能点击该链接。
- 包含了 Attacker 的 iframe、img 等。

一旦用户浏览器请求到了 Attacker，Attacker 便容易从 referer 中提取到 code 和 state，甚至可能有 access_token（例如 Implicit Flow）。

例如浏览器可能在以下 URL 渲染一个页面：

```text
https://your.site.com/auth/callback?code=xxxx-yyyy-zzzz&state
```

在该页面发起的请求 referer 中会包含 `https://your.site.com/auth/callback?code=xxxx-yyyy-zzzz&state` 内容。

**Leakage from the Authorization Server**

类似的方法，如果 Authorization Endpoint 如果包含了到 Attacker 的链接，则 Attacker 将会获取到 state。

例如浏览器可能在以下 URL 渲染一个页面：

```text
https://oauth.authorization.endpoint.com/oauth/v1/authorize?client_id=xxx&response_type=code&state=123456
```

在该页面发起的请求 referer 中会包含 `https://oauth.authorization.endpoint.com/oauth/v1/authorize?client_id=xxx&response_type=code&state=123456` 内容。

**Countermeasures**

解决措施有：

- 使用适当的 Referrer Policy 来抑制 Referer 的发送。

  ```text
  // 整个 Referer  首部会被移除。访问来源信息不随着请求一起发送。
  Referrer-Policy: no-referrer

  // 在没有指定任何策略的情况下用户代理的默认行为。
  // 在同等安全级别的情况下，引用页面的地址会被发送(HTTPS->HTTPS)，但是在降级的情况下不会被发送 (HTTPS->HTTP)。
  Referrer-Policy: no-referrer-when-downgrade

  // 在任何情况下，仅发送文件的源作为引用地址。
  // 例如  https://example.com/page.html 会将 https://example.com/ 作为引用地址。
  Referrer-Policy: origin

  // 对于同源的请求，会发送完整的URL作为引用地址，但是对于非同源请求仅发送文件的源。
  Referrer-Policy: origin-when-cross-origin

  // 对于同源的请求会发送引用地址，但是对于非同源请求则不发送引用地址信息。
  Referrer-Policy: same-origin

  // 在同等安全级别的情况下，发送文件的源作为引用地址(HTTPS->HTTPS)，但是在降级的情况下不会发送 (HTTPS->HTTP)。
  Referrer-Policy: strict-origin

  // 对于同源的请求，会发送完整的URL作为引用地址；
  // 在同等安全级别的情况下，发送文件的源作为引用地址(HTTPS->HTTPS)；在降级的情况下不发送此首部 (HTTPS->HTTP)。
  Referrer-Policy: strict-origin-when-cross-origin

  // 无论是同源请求还是非同源请求，都发送完整的 URL（移除参数信息之后）作为引用地址。
  Referrer-Policy: unsafe-url
  ```

- 避免使用 Implicit Flow 导致 Access Token 泄露。
- 使用 PKCE，让 Attacker 缺少 Code Verifier。
- code 不可反复使用，使用一次后应立即失效。
- 使用 `post response mode`，避免 URL 中存在相关参数。

### Credential Leakage via Browser History

code 和 Access Token 可能出现在浏览器访问过的 URL 历史中。

当浏览器由 AS 的重定向响应导航至 `client.example/redirection_endpoint?code=abcd`，则授权码 code 会出现在浏览器历史记录中，拥有访问该设备权限的 Attacker 可以获取到该 code。应对策略主要是：

- 避免 code 重放攻击。
- 使用 `post response mode`，避免 URL 中存在相关参数。

如果客户端已经拥有了 Access Token，则可能由于到 RS 的请求导致 Token 出现在历史记录中，例如：`provider.com/get_user_profile?access_token=abcdef`。不鼓励这样的做法，更好的方式应该是放在 HTTP Headers 中。

在 Implicit Flow 中，AS 的重定向响应导航至 `client.example/redirection_endpoint#access_token=abcdef`，则 Token 也会出现在浏览器历史记录中。应对策略主要是：

- 使用 `post response mode`，避免 URL 中存在相关参数。
- 使用 PKCE。

### Mix-Up Attacks

### Authorization Code Injection

授权码注入攻击，Attacker 会尝试窃取授权码并注入到 Attacker 自己与 Client 的会话中。简而言之就是 Attacker 截获到用的 Code 后，Attacker 使用该 Code 与 OAuth2.0 Client（例如用 code 回调 Client 的 Redirect URI） 建立会话。

如果 Attacker 不能使用授权码换取 Access Token，则这种攻击会很有效。

**攻击描述**

攻击步骤如下：

1. Attacker 在授权码流程中获取到了授权码。
1. Attacker 在自己的设备上进行 OAuth 的常规流程。
1. Attacker 向合法客户端注入自己窃取的授权码 Code（例如调用 Client 的 Callback 接口）。
1. 合法客户端向 AS 发起 Token 请求，拿到 Access Token。
1. 最终导致 Attacker 与合法客户端的会话关联到了受害者的资源上（关联到受害者的 Access Token，并可以获得受害者资源）。

**应对措施**

有两个技术方案可以解决这个问题：

- PKCE，动态生成的 code_verifier 不容易被 Attacker 获取。
- Nonce
  - 即 OIDC 的 nonce，该 nonce 是一次性使用的，由 Client 创建，并绑定到 User Agent 的会话上。
  - nonce 会通过 Authorize 请求发送给 OpenID Provider，并在 id_token 中返回该 nonce。
  - 若 Attacker 无法拿到用户 User Agent 中绑定的会话，那么注入 code 给 Client 时，就无法匹配 nonce，并被 Client 拒绝。

PKCE 是当今 OAuth 最主流的解决方案（起初只是用于 Native Application），而 nonce 适用于 OIDC Client。

### Access Token Injection

Access Token 的注入攻击是指的 Attacker 尝试向合法 Client 中注入窃取的 Access Token，这意味着 Attacker 利用 Access Token 伪造某个用户进行登录。

为了实施这样的攻击，Attacker 向 Client 发起了 Implicit Flow，并替换 AS 颁发的 Access Token 来修改授权响应。

无法在 OAuth 协议级别检测到这样的攻击，因此建议使用授权码模式进行登录，而对授权码注入攻击的考虑在 [Authorization Code Injection](#authorization-code-injection) 中阐述。

**注意：**

- 这不是 CSRF 攻击，Client 只会收到 Access Token 和 state，而 Access Token 和 state 之间没有绑定关系，所以 Client 无法判断。
- 这是针对 Access Token 注入，若是扩展一下到 ID Token，可以依赖其 nonce 来进行检测 ID Token 是否被注入。

### Cross Site Request Forgery

Attacker 可能通过受害者设备向 Client 的重定向 URL 注入请求，以此让受害者访问攻击者的资源。

**应对措施**

- 传统方案是使用 CSRF Token，并将 Token 关联到 User Agent 会话上，并将 CSRF Token 作为 state 参数传递至 AS。
- PKCE 基于生成的 code verifier 随机数，可以提供 CSRF 攻击的保护。可能受 PKCE 降级攻击，请参考 [PKCE Downgrade Attack](#pkce-downgrade-attack)。
- OIDC 授权请求的 nonce 需要绑定 User Agent 会话上，因此和 state 类似，提供了相同程度的保护。

**注意：**

- state 用于承载状态，其完整性是一个问题，Client 必须防止 state 的篡改和替换，这可以将 state 绑定到 User Agent 会话中，或者进行加密或者签名。

### PKCE Downgrade Attack

PKCE 降级攻击：对于那些实现了 PKCE 机制，但未强制要求的 AS，或者未检测当前的流程是否属于 PKCE 的 AS，具有潜在 PKCE 降级攻击的可能。

简单的说，这个攻击属于 CSRF 攻击的一个变种，其目标也是让受害者访问攻击者的资源。

具体的说，CSRF 攻击可以使用 PKCE 来进行抵御，但这种抵御可能会遭受 PKCE 降级攻击，导致 PKCE 无法抵御 CSRF 攻击。

此攻击有两个前提条件：

- Client 并未很好的使用 state 进行检查。
- AS 的 PKCE 会因为某些参数未填而关闭掉（例如没有填 code_challenge 默认不开启 PKCE 流程）。

**攻击步骤**

1. 用户使用 AS 的 Client 启动了 OAuth 会话，并且 Client 使用了 code_challenge=sha256(abc) 的 PKCE 流程，Client 正在等待 AS 的授权响应（经过 User Agent）。
1. Attacker 在自己的设备上开启 OAuth 会话，并且 Client 使用了 code_challenge=sha256(xyz)，但 Attacker 自己改造请求，删除了 code_challenge，这将导致 AS 响应的 code 没有使用 PKCE 机制。
1. Attacker 现在通过用户的 User Agent 将自己的 code 注入到 Client 的重定向 URL 上，client 会使用 code_verifier=abc 去 AS 获取 Token。
1. AS 因为判断 code 没有处于 PKCE 流程，会忽略了 code_verifier 参数，进而颁发了 Attacker 的 Access Token，完成了 CSRF 攻击。

code_verifier 通常会和 User Agent 会话绑定，因此第一步是必然的，否则 User Agent 中没有包含 code_verifier 的会话，Client 自己可能会拒绝。

**应对措施**

- state 可以很好的解决这个问题，但是 state 依赖于 Client 的实现，并且实践表明大部分 Client 都未能很好的检测 state。
- code 中必须包含 PKCE 的标识，如果开启了 PKCE，则要求 code_verifier 参数必须存在，如果没有开启 PKCE，则要求 code_verifier 一定不能存在。

### Access Token Leakage at the Resource Server

### Open Redirection

### 307 Redirect

### TLS Terminating Reverse Proxies

### Refresh Token Protection

### Client Impersonating Resource Owner

### Click jacking

## References

1. [draft-ietf-oauth-security-topics-18](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-security-topics)
1. [OAuth 2.0 Threat Model and Security Considerations](https://www.rfc-editor.org/rfc/rfc6819.html)
