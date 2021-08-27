# OAuth 2.0 Threat Model and Security Considerations

<!-- TOC -->

- [OAuth 2.0 Threat Model and Security Considerations](#oauth-20-threat-model-and-security-considerations)
  - [Overview](#overview)
    - [Attack Assumptions](#attack-assumptions)
  - [Security Features](#security-features)
    - [Tokens](#tokens)
  - [Client Threat Model](#client-threat-model)
    - [Threat: Obtaining Client Secrets](#threat-obtaining-client-secrets)
    - [Threat: Obtaining Refresh Tokens](#threat-obtaining-refresh-tokens)
    - [Threat: Obtaining Access Tokens](#threat-obtaining-access-tokens)
    - [Threat: End-User Credentials Phished Using Compromised or Embedded Browser](#threat-end-user-credentials-phished-using-compromised-or-embedded-browser)
    - [Threat: Open Redirectors on Client](#threat-open-redirectors-on-client)
  - [AuthZ Server Threat Model](#authz-server-threat-model)
    - [Threat: Password Phishing by Counterfeit Authorization Server](#threat-password-phishing-by-counterfeit-authorization-server)
    - [Threat: User Unintentionally Grants Too Much Access Scope](#threat-user-unintentionally-grants-too-much-access-scope)
    - [Threat: Malicious Client Obtains Existing Authorization by Fraud](#threat-malicious-client-obtains-existing-authorization-by-fraud)
    - [Threat: Open Redirector](#threat-open-redirector)
  - [Token Server Threat Model](#token-server-threat-model)
    - [Threat: Eavesdropping Access Tokens](#threat-eavesdropping-access-tokens)
    - [Threat: Obtaining Access Tokens from Authorization Server Database](#threat-obtaining-access-tokens-from-authorization-server-database)
    - [Threat: Disclosure of Client Credentials during Transmission](#threat-disclosure-of-client-credentials-during-transmission)
    - [Threat: Obtaining Client Secret from Authorization Server Database](#threat-obtaining-client-secret-from-authorization-server-database)
    - [Threat: Obtaining Client Secret by Online Guessing](#threat-obtaining-client-secret-by-online-guessing)
  - [Security Considerations](#security-considerations)
    - [General](#general)
      - [Credentials](#credentials)
        - [Online Attacks on Secrets](#online-attacks-on-secrets)
      - [Tokens (Access, Refresh, Code)](#tokens-access-refresh-code)
        - [Limit Token Scope](#limit-token-scope)
        - [Determine Expiration Time](#determine-expiration-time)
        - [Use Short Expiration Time](#use-short-expiration-time)
        - [Limit Number of Usages or One-Time Usage](#limit-number-of-usages-or-one-time-usage)
        - [Sign Self-Contained Tokens](#sign-self-contained-tokens)
        - [Encrypt Token Content](#encrypt-token-content)
        - [Adopt a Standard Assertion Format](#adopt-a-standard-assertion-format)
      - [Access Tokens](#access-tokens)
    - [Authorization Server](#authorization-server)
      - [Refresh Tokens](#refresh-tokens)
        - [Binding of Refresh Token to "client_id"](#binding-of-refresh-token-to-client_id)
        - [Refresh Token Rotation](#refresh-token-rotation)
        - [Revocation of Refresh Tokens](#revocation-of-refresh-tokens)
        - [Device Identification](#device-identification)
      - [Client Authentication and Authorization](#client-authentication-and-authorization)
        - [Don't Issue Secrets to Clients with Inappropriate Security Policy](#dont-issue-secrets-to-clients-with-inappropriate-security-policy)
        - [Require User Consent for Public Clients without Secret](#require-user-consent-for-public-clients-without-secret)
        - [Issue Installation-Specific Client Secrets](#issue-installation-specific-client-secrets)
        - [Revoke Client Secrets](#revoke-client-secrets)
        - [Use Strong Client Authentication](#use-strong-client-authentication)
    - [Client App Security](#client-app-security)
      - [Use Standard Web Server Protection Measures](#use-standard-web-server-protection-measures)
      - [Store Secrets in Secure Storage](#store-secrets-in-secure-storage)
      - [Utilize Device Lock to Prevent Unauthorized Device Access](#utilize-device-lock-to-prevent-unauthorized-device-access)
  - [References](#references)

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

AuthZ Server 的 expires_in 响应参数用于限制访问令牌生命周期。

颁发一个短期的访问令牌，可以减少访问令牌泄漏时带来的影响。

**Access Token**

**Refresh Token**

刷新令牌代表某个 Client 拥有访问 Owner 资源的长期权限，该令牌仅在 Client 和 AuthZ Server 之间交换。

Client 使用刷新令牌去获取新的访问 Resource Server 的访问令牌。

**Authorization "code"**

一个授权码，代表一次成功授权的中间过程，客户端使用授权码去获得访问令牌和刷新令牌。添加这个中间过程，而不直接将令牌重定向至第三方 Redirect URI，出于两个目的：

1. 浏览器的流程中，URI 查询参数更容易暴露给潜在的攻击者，例如通过浏览器缓存、历史记录、日志等。为了减少这种威胁，传递短期授权码而不是访问令牌。
2. Client 直接向 AuthZ Server 请求更容易校验 Client 的身份（使用 Client Secret）。

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

**攻击：从源代码或二进制文件中获取 Client Secret**

对策：

- 不要向公共客户端或具有不适当安全策略的客户端发布 Client Secret。请参考：[Don't Issue Secrets to Clients with Inappropriate Security Policy](#dont-issue-secrets-to-clients-with-inappropriate-security-policy)。
- 公共客户端需要用户同意。请参考：[Require User Consent for Public Clients without Secret](#require-user-consent-for-public-clients-without-secret)。
- 使用特定于部署的 Client Secret。请参考：[Issue Installation-Specific Client Secrets](#issue-installation-specific-client-secrets)。
- 撤销 Client Secret。请参考：[Revoke Client Secrets](#revoke-client-secrets)。

**攻击：从特定于部署的 Client 中获得 client Secret**

对策：

- Web server: Apply standard web server protection measures，请参考。
- Native applications: Store secrets in secure local storage，请参考：[Store Secrets in Secure Storage](#store-secrets-in-secure-storage)。
- 撤销 Client Secret。请参考：[Revoke Client Secrets](#revoke-client-secrets)。

### Threat: Obtaining Refresh Tokens

根据不同的 Client 类型，刷新令牌可能会以不同的方式泄露给攻击者，本节提供了应对刷新令牌泄露措施。

这是一些普遍的应对策略：

- Token Endpoint 将刷新令牌和第三方应用标识 (client_id) 绑定，请参考：[Binding of Refresh Token to "client_id"](#binding-of-refresh-token-to-client_id)。
- 限制 Token 的 scope 范围，请参考：[Limit Token Scope](#limit-token-scope)。
- 支持撤销刷新令牌，请参考：[Revocation of Refresh Tokens](#revocation-of-refresh-tokens)。
- 支持撤销第三方应用凭证，请参考：[Revoke Client Secrets](#revoke-client-secrets)。
- 刷新令牌可以自动轮替，请参考：[Refresh Token Rotation](#refresh-token-rotation)。

这是一些典型攻击：

**攻击：从 Web App 获取刷新令牌**

攻击者可能突破了 Web 服务器的网络安全策略，监听了 Web 服务器的网络。

这个影响是非常大的，由于 Web 应用程序管理某个站点的用户帐户，因此此类攻击将导致该站点上的所有刷新令牌暴露给攻击者。

对策：

- 标准的 Web 服务器保护措施，请参考：[Use Standard Web Server Protection Measures](#use-standard-web-server-protection-measures)。
- 使用更强的客户端认证技术，例如 client_assertion/ client_token，这些基于公钥的技术，将使攻击者即便拿到了访问令牌也无法申请访问令牌，请参考：[Use Strong Client Authentication](#use-strong-client-authentication)。

**攻击：从 Native App 获取刷新令牌**

对于 Native App，我们使用 PKCE 流程进行授权，此时刷新令牌通常会保存在本地设备上。

攻击者可以尝试获取设备上的文件系统访问权限，并读取刷新令牌。 

对策：

- 将机密在本地进行安全存储，请参考：[Store Secrets in Secure Storage](#store-secrets-in-secure-storage)。
- 利用设备锁，阻止未授权设备的访问，请参考：[Utilize Device Lock to Prevent Unauthorized Device Access](#utilize-device-lock-to-prevent-unauthorized-device-access)。

**攻击：窃取设备**

设备（例如移动电话）可能被盗。 在这种情况下，攻击者可以以合法用户的身份访问所有应用程序。

对策：

- 利用设备锁，阻止未授权设备的访问，请参考：[Utilize Device Lock to Prevent Unauthorized Device Access](#utilize-device-lock-to-prevent-unauthorized-device-access)。
- 若用户知道自己设备被盗，他们可以撤销掉受影响令牌，请参考：[Revocation of Refresh Tokens](#revocation-of-refresh-tokens)。

**攻击：克隆设备**

所有设备数据和应用程序都被复制到另一台设备。 应用程序在目标设备上按原样使用。

对策：

- 利用设备锁来防止未经授权的设备访问，请参考：[Utilize Device Lock to Prevent Unauthorized Device Access](#utilize-device-lock-to-prevent-unauthorized-device-access)。

- 将刷新令牌请求与设备标识相结合，请参考：[Device Identification](#device-identification)。

- 刷新令牌轮换，请参考 [Refresh Token Rotation](#refresh-token-rotation)。

- 如果用户知道设备已被克隆，他们可以撤销刷新令牌，请参考 [Revocation of Refresh Tokens](#revocation-of-refresh-tokens)。

### Threat: Obtaining Access Tokens

根据客户端类型，访问令牌可能会以不同的方式暴露给攻击者。

如果应用将访问令牌存储在其他应用可以访问设备中，则其他应用可能会窃取访问令牌。

对策：

- 将访问令牌存储在内存中，请参考：[Access Tokens](#access-tokens)。
- 限制令牌的 scope，请参考：[Limit Token Scope](#limit-token-scope)。
- 保持令牌在内存中，并采取和刷新令牌相同的保护措施，请参考：[Refresh Tokens](#refresh-tokens)。
- 保持访问令牌生命周期足够短，请参考：[Use Short Expiration Time](#use-short-expiration-time)。

### Threat: End-User Credentials Phished Using Compromised or Embedded Browser

### Threat: Open Redirectors on Client

## AuthZ Server Threat Model

### Threat: Password Phishing by Counterfeit Authorization Server

### Threat: User Unintentionally Grants Too Much Access Scope

### Threat: Malicious Client Obtains Existing Authorization by Fraud

### Threat: Open Redirector

## Token Server Threat Model

Token Endpoint 存在以下的威胁：

### Threat: Eavesdropping Access Tokens

攻击者可能尝试窃听 Token Endpoint 传输到 Client 的访问令牌。

对策：

- 必须使用 TLS。
- 如果无法保证端到端的机密性，可以减少访问令牌的 scope 和生命周期减少泄露时的影响。

### Threat: Obtaining Access Tokens from Authorization Server Database

### Threat: Disclosure of Client Credentials during Transmission

### Threat: Obtaining Client Secret from Authorization Server Database

### Threat: Obtaining Client Secret by Online Guessing

攻击者通过在线猜测，导致猜出来了有效的 client_id/client_secret 对。

对策：

- 使用高熵的 client_secret，请参考：[Online Attacks on Secrets](#online-attacks-on-secrets)。
- Lock Accounts，即多次尝试失败后，锁定住相应的 client，不允许再试，请参考：[Online Attacks on Secrets](#online-attacks-on-secrets)。
- 使用更强的 Client 认证方案，请参考：[Use Strong Client Authentication](#use-strong-client-authentication)。

**注意：**

- 在线猜测的意思是不停的换 client_id 和 client_secret 发请求，遍历所有的可能。

## Security Considerations

### General

这是一些通用的安全考虑。

#### Credentials

##### Online Attacks on Secrets

**Utilize Secure Password Policy**

**Use High Entropy for Secrets**

当创建不供人类用户使用的机密（例如，客户端机密或令牌句柄）时，授权服务器应包含合理级别的熵以降低猜测攻击的风险。

通常令牌值长度应该 >=128 bits。

**Lock Accounts**

通过在一定次数的尝试失败后锁定相应的帐户，可以减轻对密码的在线攻击。

注意：此措施可能会被滥用以锁定合法服务用户。

#### Tokens (Access, Refresh, Code)

这里是针对访问令牌，刷新令牌，授权码的安全考虑。

##### Limit Token Scope

Token Endpoint 可以减少或限制令牌的权限。

这可以减少以下威胁的影响：

- 令牌泄露。
- 向恶意应用颁发了令牌。
- 避免颁发了权限过大的令牌。

##### Determine Expiration Time

##### Use Short Expiration Time

使用短周期的访问令牌，是防止以下威胁的手段：

- 重放攻击
- 令牌泄露
- 在线猜测

**注意：**

- Token Endpoint 和 Resource Endpoint 之间的服务器时间精确同步
- 较短的生命周期，可能涉及到更多的令牌刷新和用户授权

##### Limit Number of Usages or One-Time Usage

##### Sign Self-Contained Tokens

对于内容自包含的令牌，必须进行签名，以检测是否被篡改，或者被伪造，签名的方式通常有：

- 基于消息的 HMAC

##### Encrypt Token Content

出于保密的原因或者保护系统内部数据，自包含令牌可能是进行加密，而非签名。

根据令牌的类型，密钥可能再服务器节点之间进行分发，分发方式由使用的密钥管理模型来确定。

##### Adopt a Standard Assertion Format

对于使用断言式令牌的 OAuth2.0 系统，强烈建议采用标准的断言格式：

- SAML
- JWT
  
#### Access Tokens

以下的措施应该进行实施：

- Keep them in transient memory (accessible by the client application only).
- 使用 TLS 进行通信。
- 确保客户端不与其他第三方共享令牌。


### Authorization Server

#### Refresh Tokens

本节描述了刷新令牌的一些安全考虑。

##### Binding of Refresh Token to "client_id"

Token Endpoint 在颁发刷新令牌时，应该将 client_id 和刷新令牌进行绑定。

当令牌刷新请求发出时：

```sh
curl "https://oauth.domain.com/token" -d '
grant_type=<refresh_token>&
client_id=<client_id>&
client_secret=<client_secret>&
refresh_token=<refresh_token>&
scope=<scope>'
```

Endpoint 应该先校验刷新令牌的 client_id 是否与请求中的一致，再校验第三方应用凭证。

##### Refresh Token Rotation

刷新令牌自动轮替，可以检测不同的 client 使用相同的刷新令牌。

基本的想法是：每次刷新令牌请求，都更改刷新令牌的值，并且将旧的刷新令牌强制过期。

当 Token Endpoint 检测到尝试使用旧刷新令牌的访问，由于无法确定是攻击者还是合法第三方应用的访问，因此此类场景下，有效的刷新令牌以及相关的访问授权都会被撤销。

##### Revocation of Refresh Tokens

Token Endpoint 允许第三方应用或者用户明确撤销刷新令牌，令牌的撤销有一套标准 RFC 提供：[OAuth 2.0 Token Revocation](https://datatracker.ietf.org/doc/html/rfc7009)。

##### Device Identification

> The authorization server may require the binding of authentication credentials to a device identifier.  The International Mobile Station Equipment Identity [IMEI] is one example of such an identifier; there are also operating system-specific identifiers.  The authorization server could include such an identifier when authenticating user credentials in order to detect token theft from a particular device.

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

**注意：**

- 此措施将立即使发给相应客户端的任何授权码或刷新令牌无效。
- 这可能会无意中影响跨特定本机或 Web 应用程序的多个部署使用的客户端标识符和机密。

##### Use Strong Client Authentication

通过使用 Client 断言的形式进行客户端身份认证，这样可以消除了 client_secret 分发的需要。

在注册前，Client 会生成私钥和公钥，并在注册时将公钥交给 OAuth2.0 系统，通常该方式要求 Client 安全存储生成断言签名的私钥。

可以参考 [Assertion Framework for OAuth 2.0 Client Authentication and Authorization Grants](https://datatracker.ietf.org/doc/html/rfc7521)。

### Client App Security

客户端应用的安全策略。

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

- 从安全存储中读取机密数据，数据保存在应用程序的本地内存中是相对安全的，因为本地内存的数据不容易泄漏。

#### Utilize Device Lock to Prevent Unauthorized Device Access

在典型的现代手机上，有许多 “设备锁” 选项可以提供额外的保护，以保障设备被盗或放错时的安全性，这些设备锁安全措施包括：

- PIN 码
- 密码
- 生物识别功能，例如指纹识别和面部识别


## References

1. [Assertion Framework for OAuth 2.0 Client Authentication and Authorization Grants](https://datatracker.ietf.org/doc/html/rfc7521)