# OAuth 2.0 Threat Model and Security Considerations

<!-- TOC -->

- [OAuth 2.0 Threat Model and Security Considerations](#oauth-20-threat-model-and-security-considerations)
  - [Overview](#overview)
    - [Attack Assumptions](#attack-assumptions)
  - [Security Features](#security-features)
    - [Tokens](#tokens)
      - [Limited Access Token Lifetime](#limited-access-token-lifetime)
      - [Access Token](#access-token)
      - [Refresh Token](#refresh-token)
    - [Authorization "code"](#authorization-code)
  - [Client Threat Model](#client-threat-model)
    - [Threat: Obtaining Client Secrets](#threat-obtaining-client-secrets)
    - [Threat: Obtaining Refresh Tokens](#threat-obtaining-refresh-tokens)
    - [Threat: Obtaining Access Tokens](#threat-obtaining-access-tokens)
    - [Threat: End-User Credentials Phished Using Compromised or Embedded Browser](#threat-end-user-credentials-phished-using-compromised-or-embedded-browser)
    - [Threat: Open Redirectors on Client](#threat-open-redirectors-on-client)
  - [AuthZ Server Threat Model](#authz-server-threat-model)
  - [Token Server Threat Model](#token-server-threat-model)
  - [Security Considerations](#security-considerations)
    - [Authorization Server](#authorization-server)
      - [Client Authentication and Authorization](#client-authentication-and-authorization)
        - [Don't Issue Secrets to Clients with Inappropriate Security Policy](#dont-issue-secrets-to-clients-with-inappropriate-security-policy)
        - [Require User Consent for Public Clients without Secret](#require-user-consent-for-public-clients-without-secret)
        - [Issue Installation-Specific Client Secrets](#issue-installation-specific-client-secrets)
        - [Revoke Client Secrets](#revoke-client-secrets)
    - [Client App Security](#client-app-security)
      - [Use Standard Web Server Protection Measures](#use-standard-web-server-protection-measures)
      - [Store Secrets in Secure Storage](#store-secrets-in-secure-storage)

<!-- /TOC -->

## Overview

本文主要参考 [RFC 6819](https://www.rfc-editor.org/rfc/rfc6819.html)。

RFC 主要内容是：

- Documents any assumptions and scope considered when creating the threat model.
- Describes the security features built into the OAuth protocol and ow they are intended to thwart attacks.
- Gives a comprehensive threat model for OAuth and describes the respective countermeasures to thwart those threats.

RFC 6819 主要针对 OAuth 核心规范，对于其扩展性的规范安全性仍在讨论中。

### Attack Assumptions

我们假设攻击者是这样的：

- 攻击者可以完全访问 Client 和 AuthZ Server 之间的网络，以及 Client 和 Resource Server 之间的网络。攻击者不能访问 AuthZ Server 和 Resource Server 之间的网络。
- 攻击者拥有无限的资源发起攻击。
- OAuth2.0 涉及的三方中，其中两个方可能串通起来向第三方发起攻击。例如 Client 和 AuthZ Server 可能被攻击者控制，串通起来获取用户资源的访问权限。

## Security Features

这是一些 OAuth2.0 协议内置的特征，以减轻攻击和安全问题。

### Tokens

OAuth2.0 存在多种令牌：访问令牌、刷新令牌、授权码。令牌信息有两种表现形式：

Represented | Description | Recommand
-|-|-
Handle | 句柄式令牌，这是对令牌内部数据的引用，类似于一个 session_id。这种令牌是不透明的，消费方无法去解析令牌信息，而是需要依赖于发布方。句柄方式容易实现撤销。| 当消费方和发布方在同一实体中时，推荐该方法。如果消费方和发布方并不在同一实体中，其通信成本是需要考虑的。
Assertion | 断言式令牌，消费者可解析。通常具有持续时间、受众，并且经过数字签名以确保数据完整性和来源身份验证。例如 SAML、JWT 等。| 消费方和发布方无需和实体通信便可以使用。因为缺少和发布方的通信，因此撤销会实现的更困难。

使用令牌的方式也有两种：

Type | Description
-|-
Bearer Token | 不记名令牌是任何收到令牌的客户端都可以使用的令牌。<br>因为仅仅拥有就足以使用令牌，所以确保端点之间的通信安全以确保只有经过授权的端点可以捕获令牌是很重要的。
Proof Token | 证明令牌只能由特定的客户端持有，每次使用该令牌，都需要由客户端证明自己。例如 JWT Pop Token。

#### Limited Access Token Lifetime

AuthZ Server 的 expires_in 响应参数用于限制访问令牌生命周期。

颁发一个短期的访问令牌，可以减少访问令牌泄漏时带来的影响。

#### Access Token

#### Refresh Token

刷新令牌代表某个 Client 拥有访问 Owner 资源的长期权限，该令牌仅在 Client 和 AuthZ Server 之间交换。

Client 使用刷新令牌去获取新的访问 Resource Server 的访问令牌。

### Authorization "code"

一个授权码，代表一次成功授权的中间过程，客户端使用授权码去获得访问令牌和刷新令牌。添加这个中间过程，而不直接将令牌重定向至第三方 Redirect URI，出于两个目的：

1. 浏览器的流程中，URI 查询参数更容易暴露给潜在的攻击者，例如通过浏览器缓存、历史记录、日志等。为了减少这种威胁，传递短期授权码而不是访问令牌。
1. Client 直接向 AuthZ Server 请求更容易校验 Client 的身份（使用 Client Secret）。

## Client Threat Model

这部分描述在 OAuth2.0 Client 中可能存在的安全威胁。

### Threat: Obtaining Client Secrets

攻击者可能尝试获取一个特定客户端的 Client Secret，目的通常是：

- 以便重放 Refresh Token 和授权码。
- 代表受攻击的客户端获取令牌，并具有作为客户端实例的 “client_id” 的特权。

由此产生的影响：

- 可以绕过 AuthZ Server 的 Client 身份验证。
- 可以重播被盗的刷新令牌或授权码。

根据不同客户端的类型，以下的攻击方式可能会被用于获取 Client Secret。

- 攻击：从源代码或二进制文件中获取 Client Secret。
  - 对策：
    - 不要向公共客户端或具有不适当安全策略的客户端发布 Client Secret。请参考：[Don't Issue Secrets to Clients with Inappropriate Security Policy](#dont-issue-secrets-to-clients-with-inappropriate-security-policy)。
    - 公共客户端需要用户同意。请参考：[Require User Consent for Public Clients without Secret](#require-user-consent-for-public-clients-without-secret)。
    - 使用特定于部署的 Client Secret。请参考：[Issue Installation-Specific Client Secrets](#issue-installation-specific-client-secrets)。
    - 撤销 Client Secret。请参考：[Revoke Client Secrets](#revoke-client-secrets)。
- 攻击：从特定于部署的 Client 中获得 client Secret。
  - 对策：
    - Web server: Apply standard web server protection measures，请参考。
    - Native applications: Store secrets in secure local storage，请参考：[Store Secrets in Secure Storage](#store-secrets-in-secure-storage)。
    - 撤销 Client Secret。请参考：[Revoke Client Secrets](#revoke-client-secrets)。

### Threat: Obtaining Refresh Tokens

### Threat: Obtaining Access Tokens

### Threat: End-User Credentials Phished Using Compromised or Embedded Browser

### Threat: Open Redirectors on Client

## AuthZ Server Threat Model

## Token Server Threat Model

## Security Considerations

### Authorization Server

#### Client Authentication and Authorization

##### Don't Issue Secrets to Clients with Inappropriate Security Policy

AuthZ Server 不应该向 Public Client 发布 Client Secret，否则这降低了服务器将客户端视为经过强身份验证的可能性。

创建由本地所有 Client 共享的 Client ID/Secret 的好处有限，这种情况下不应该将 Client ID/Secert 写到源代码或资源包中，因为这容易受到逆向攻击。

这种情况要求开发者必须通过相应的分发渠道（例如应用程序市场）将此秘密传输到最终用户设备上的所有应用程序安装。

由于授权服务器无法真正信任客户端的标识符，因此向最终用户指示客户端的可信度将是危险的。

##### Require User Consent for Public Clients without Secret

AuthZ Server 不允许 Public Client 的自动授权，而是所有授权都得到用户的批准。

这样，假冒的 Public Client 将交给用户进行识别。

##### Issue Installation-Specific Client Secrets

AuthZ Server 可以对不同的 Client 分发隔离的 Client ID/Secret，因为每个 Client 都使用不同的 Client 凭证，因此这样的方法可以将原本的 Public Client 变回至 confidential Client。

对于 Native Application，因为任何设备上的每个副本都是不同的安装。在这种情况下安装特定的秘密将需要获得“client_id”和“client_secret”

1. 从应用市场下载过程中，或
1. 在设备上安装期间。

这两种方法都需要一种自动机制来发布客户端 ID 和机密，目前 OAuth 未定义该机制。

##### Revoke Client Secrets

AuthZ Server 可以撤销 Client Secret，以防止滥用泄露的 Secret。

注意：此措施将立即使发给相应客户端的任何授权码或刷新令牌无效。 这可能会无意中影响跨特定本机或 Web 应用程序的多个部署使用的客户端标识符和机密。

### Client App Security

#### Use Standard Web Server Protection Measures

> Use standard web server protection and configuration measures to protect the integrity of the server, databases, configuration files    and other operational components of the server.

使用标准的 Web 服务器保护和配置措施来保护服务器、数据库、配置文件和服务器的其他操作组件的完整性。

#### Store Secrets in Secure Storage

有不同的方法可以在设备或服务器上安全地存储各种类型的机密（令牌、客户端机密）。

- 大多数 PC 操作系统将不同系统用户的个人存储区分开来。
- 大多数 Mobile 支持将特定于应用程序的数据存储在文件系统的不同区域，并保护数据不被其他应用程序访问。
- 应用程序可以通过使用用户提供的机密（例如 PIN 或密码）来实现机密数据。

另一种选择是将刷新令牌交换到受信任的 Server。 这个选择需要 Client 和 Server 之间的身份验证。

**注意：**

- 即使从安全存储中读取机密数据，应用程序也应确保机密数据保持机密，这通常意味着将此数据保存在应用程序的本地内存中（本地内存的数据不容易泄漏）。
