# Openssl RSA

<!-- TOC -->

- [Openssl RSA](#openssl-rsa)
    - [概览](#概览)
    - [RSA 原理](#rsa-原理)
    - [密钥编码](#密钥编码)
        - [ASN.1](#asn1)
        - [DER](#der)
        - [PEM](#pem)
        - [PKCS](#pkcs)
            - [PKCS 1](#pkcs-1)
            - [PKCS 8](#pkcs-8)
    - [Openssl 命令](#openssl-命令)
    - [PEM 与 ne 转换](#pem-与-ne-转换)
    - [参考文献](#参考文献)

<!-- /TOC -->

## 概览

本文主要记录了 RSA 基本知识、存储和传输格式以及 Openssl RSA 命令（后续如果有时间会补充 Openssl RSA 编程），以便快速查阅和回顾。

RSA 算法会生成公钥和私钥，公钥加密的数据可以使用私钥解密，私钥加密的数据可以用于解密。

公钥加密通常用于加密通信，私钥加密通常用于身份认证，本文并不会细数 RSA 在加密通信和身份认证中的应用。

## RSA 原理

RSA 算法会生成公钥和私钥，公钥加密的数据可以使用私钥解密，私钥加密的数据可以用于解密。

RSA 的公钥有两个变量（整数）确定：n 和 e。
RSA 的私钥也有两个变量（整数）确定：n 和 d。

使用公钥数据加密：

```txt
m^e mod n = c
```

- m 原始数据
- c 加密数据
- e 公钥 e
- n 公钥 n

使用私钥数据解密：

```txt 
c^d mod n = m
```

- c 加密数据
- m 解密数据
- d 私钥 d
- n 私钥 n

**注意：**

- 公钥 n 和 私钥 n 是相等的。

算法的原理细节可以参考阮一峰的 [RSA 算法原理（一）](http://www.ruanyifeng.com/blog/2013/06/rsa_algorithm_part_one.html) 和 [RSA 算法原理（二）](http://www.ruanyifeng.com/blog/2013/07/rsa_algorithm_part_two.html)

## 密钥编码

通过对密钥进行编码，可以方便密钥的存储和传输，并为了让不同系统以统一的方式去解析密钥，对此编码方式进行了标准化。

RSA 的密钥的编码会涉及到以下标准：

- [ASN.1](#asn1) 用于定义和描述独立于特定计算机硬件的对象结构。属于 [X.680](https://www.itu.int/rec/T-REC-X.680) 标准。
- [DER](#der) 用于将 ASN.1 描述的对象编码为具体的数据流规则。是 [X.690](https://www.itu.int/rec/T-REC-X.690/) 标准的一部分。
- [PEM](#pem) 为了方便 ASCII 系统中传输和存储密钥而定义的一种格式化标准。PEM 格式最终由 [RFC 7468](https://tools.ietf.org/html/rfc7468) 标准确定。
- [PKCS](#pkcs) 公钥密码学标准，由多个部分组成。对于 RSA，我们需要关心的是 PKCS #1 以及 PKCS #8：
  - PKCS #1，通过 ASN.1 定义的 RSA 公钥和私钥的格式。
  - PKCS #8，通过 ASN.1 定义的 通用密钥格式。相比于 #1 仅用于 RSA，#8 可以用于多种密码学算法的密钥。

**注意：**

- 为了保障 RSA 公钥的安全性，还需要[公钥基础设施](https://en.wikipedia.org/wiki/Public_key_infrastructure)（Public key infrastructure, PKI）。

### ASN.1

Abstract Syntax Notation One (ASN.1) 用于定义和描述独立于特定计算机硬件的对象结构，允许设计人员在协议数据单元中定义参数，而无需担心如何编码以进行传输。

*ASN.1 Wiki:*

> Abstract Syntax Notation One (ASN.1) is a standard interface description language for defining data structures that can be serialized and deserialized in a cross-platform way. It is broadly used in telecommunications and computer networking, and especially in cryptography.

ASN 中的 1 是为了方便后续强化 ASN，以得到 ASN.2、ASN.3 等等，当然仅在真的有必要时才会有 ASN.2 等后续版本（目前仅有 ASN.1）。

*The Tutorial and Reference by Doug Steedman:*

> The "One" was added to the ASN name by ISO to leave open the future possibility of a better language for expressing abstract syntaxes. However, an "ASN.2", should it ever be considered necessary, will have to be significantly more powerful than ASN.1 to be worth inventing.

这是 PKCS #1 中使用 ASN.1 对公钥的定义：

```asn
RSAPublicKey ::= SEQUENCE {
    modulus           INTEGER,  -- n
    publicExponent    INTEGER   -- e
}
```

如需 ASN.1 更详细的语法细节，请参考 [X.680](https://www.itu.int/rec/T-REC-X.680)。

### DER

DER (Distinguished Encoding Rules) 是 ASN.1 转换为可存储和传输数据的一种编码规则，属于 X.690 的一部分。DER 具体的规则请参考[X.690](https://www.itu.int/rec/T-REC-X.690)。

X.690 一共包括三种编码规则：

- BER(Basic Encoding Rules)
- CER(Canonical Encoding Rules)
- DER(Distinguished Encoding Rules)

最初 X.690 仅有 BER，后续又加入了 BER 的两个子集即 DER 和 CER。BER、DER、CER 之间的区别主要在于灵活性上。

*X.609 Wiki:*

> The key difference between the BER format and the CER or DER formats is the flexibility provided by the Basic Encoding Rules.

CER 和 DER 作为 BER 的子集，对 BER 做了的限制，虽然降低了灵活性，但是也消除了 BER 中的歧义。

*X.609 Wiki:*

> A receiver must be prepared to accept all legal encodings in order to legitimately claim BER-compliance. By contrast, both CER and DER restrict the available length specifications to a single option. As such, CER and DER are restricted forms of BER and serve to disambiguate the BER standard.

CER 和 DER 的区别主要是对发送方做的限制不同。

*X.609 Wiki:*

> CER and DER differ in the set of restrictions that they place on the sender. The basic difference between CER and DER is that DER uses definitive length form and CER uses indefinite length form in some precisely defined cases. That is, DER always has leading length information, while CER uses end-of-contents octets instead of providing the length of the encoded data. Because of this, CER requires less metadata for large encoded values, while DER does it for small ones.


DER 被用作最流行的编码格式，用于在文件中存储 X.509 证书。这些证书 DER 文件是二进制文件，无法使用文本编辑器查看。DER 编码得到的文件常见的后缀名有：

- `.der`，该后缀的文件一定是 DER 编码。
- `.cer`，需要注意的是 DER 文件可以用 `.cer` 后缀，但是并非所有的 `.cer` 都是 DER 编码，也有可能是 [PEM](#pem)。

除了证书外，RSA 的公钥私钥也可以通过 DER 编码进行存储和传输。

### PEM

虽然通过 DER 已经可以得到 ASN.1 的编码数据，可以进行存储和传输，但是为了方便在 ASCII 系统（例如邮件）中进行传递和存储，又提出了 PEM 格式。

PEM（增强隐私的邮件，Privacy-Enhanced Mail），该协议的初衷是在邮件中传递 DER 二进制数据，但是其文本编码格式广泛应用于各个领域。

PEM 格式本质上是 DER 二进制数据进行 Base64 编码后得到的文本，并且附加页眉和页脚，以区分 DER 界限：

- 页眉："----- BEGIN {LABEL} -----"。
- 页脚："----- END {LABEL} -----"。
- 不同类型的 DER，页眉页脚中的 LABEL 并不相同。

这是一个 PEM 示例：

```pem
-----BEGIN PUBLIC KEY-----
MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAwZRDlZWn26KWf5BPnh4U
dLxfqoNLnq/9GAhnmN/wUsZf936LKgMLE30cu576QitlqIO69dZ7WDPysfBcxA3H
7UhlEtLtLNMnEFhKieU2GP2D2KPAHk/fdo2f+va9KIt6Nww3yiyIN6qM2s3hd/HL
SLZEfvGoKPvucZ/12x4XaAVGPgNWAnf/hu36iHeqE2AHrUFiCiijSPfVQ3x8PIcx
goffFoxVlPob+vMBjRDjNlHappAz/Cm46sKPdQ/ntLjoL+fLVcgnkYQ18bQizqIB
xnFDs65x0k8WPoJL2PdILBebUQXs/Q3MtvDOUhwLWpNIJoDM4DmZmYzeXns3RLr+
HQIDAQAB
-----END PUBLIC KEY-----
```

### PKCS

公钥密码学标准（Public Key Cryptography Standards, PKCS）。

虽然 PKCS 这里名称指的是 “公钥”，但实际上 PKCS 同时规定了公钥和私钥。

#### PKCS 1

PKCS #1 被称为 RSA Cryptography Specifications，定义了 RSA 加密技术相关标准。这里仅列出 PKCS #1 中密钥语法。

- PKCS #1 RSA 公钥：
  - ASN.1：

    ```asn
    RSAPublicKey ::= SEQUENCE {
        modulus           INTEGER,  -- n
        publicExponent    INTEGER   -- e
    }
    ```

  - PEM 格式（其中 BASE64 ENCODED DATA 是 DER 的 Base64）：

    ```txt
    -----BEGIN RSA PUBLIC KEY-----
    BASE64 ENCODED DATA
    -----END RSA PUBLIC KEY-----
    ```

- PKCS #1 RSA 私钥：
  - ASN.1：

    ```asn
    RSAPrivateKey ::= SEQUENCE {
        version           Version,
        modulus           INTEGER,  -- n
        publicExponent    INTEGER,  -- e
        privateExponent   INTEGER,  -- d
        prime1            INTEGER,  -- p
        prime2            INTEGER,  -- q
        exponent1         INTEGER,  -- d mod (p-1)
        exponent2         INTEGER,  -- d mod (q-1)
        coefficient       INTEGER,  -- (inverse of q) mod p
        otherPrimeInfos   OtherPrimeInfos OPTIONAL
    }
    ```

 - PEM 格式（其中 BASE64 ENCODED DATA 是 DER 的 Base64）：

    ```txt
    -----BEGIN RSA PRIVATE KEY-----
    BASE64 ENCODED DATA
    -----END RSA PRIVATE KEY-----
    ```

更多细节请参考 [Public-Key Cryptography Standards (PKCS) #1](https://tools.ietf.org/html/rfc3447#section-9)。

#### PKCS 8

PKCS #8 Private-Key Information Syntax Standard，是私钥信息语法规范，不局限于 RSA，可以对多种私钥进行描述。

PKCS #8 中对于私钥提供了进一步加密的安全性保障。

- PKCS #8 公钥：

  - ASN.1

    ```asn
    PublicKeyInfo ::= SEQUENCE {
        algorithm       AlgorithmIdentifier,
        PublicKey       BIT STRING
    }

    AlgorithmIdentifier ::= SEQUENCE {
        algorithm       OBJECT IDENTIFIER,
        parameters      ANY DEFINED BY algorithm OPTIONAL
    }
    ```

    - 其中 algorithm 标识了采用的算法，如 RSA、AES。 
    - 其中 PublicKey 是 PKCS #1 的 RSA 公钥 BER（若 Algorithm 是 RSA）。

  - PEM

    ```txt
    -----BEGIN PUBLIC KEY-----
    BASE64 ENCODED DATA
    -----END PUBLIC KEY-----
    ```

- PKCS #8 私钥：

  - 未加密私钥：
  
    - ASN.1

      ```asn
      PrivateKeyInfo ::= SEQUENCE {
          version         Version,
          algorithm       AlgorithmIdentifier,
          PrivateKey      BIT STRING
      }
  
      AlgorithmIdentifier ::= SEQUENCE {
          algorithm       OBJECT IDENTIFIER,
          parameters      ANY DEFINED BY algorithm OPTIONAL
      }
      ```

      - 其中 algorithm 标识了采用的算法，如 RSA、AES。 
      - 其中 PrivateKey 是 PKCS #1 的 RSA 私钥 BER。
    
    - PEM

      ```txt
      -----BEGIN PRIVATE KEY-----
      BASE64 ENCODED DATA
      -----END PRIVATE KEY-----
      ```

  - 加密私钥：

    - ASN.1

      ```ans
      EncryptedPrivateKeyInfo ::= SEQUENCE {
          encryptionAlgorithm  EncryptionAlgorithmIdentifier,
          encryptedData        EncryptedData
      }

      EncryptionAlgorithmIdentifier ::= AlgorithmIdentifier

      EncryptedData ::= OCTET STRING
      ```

      - 其中 encryptionAlgorithm 标识对私钥进行加密的加密算法。
      - 其中 encryptedData 是私钥加密后的数据。原始数据是 PKCS #8 的未加密信息，即上文中的 `PrivateKeyInfo`。
      - 加密的私钥受 Password 保护，在 Openssl 中生成加密私钥时会要求输入 Password，在使用加密私钥时也要求输入 Password。

    - PEM

      ```txt
      -----BEGIN ENCRYPTED PRIVATE KEY-----
      BASE64 ENCODED DATA
      -----END ENCRYPTED PRIVATE KEY-----
      ```


**注意：**

- 虽然 PKCS #8 是私钥标准，但其实也定义了公钥。

## Openssl 命令

openssl 的 rsa 命令通常以 `openssl rsa` 或 `openssl genrsa` 开头。

- 查看 PEM 文件中的密钥信息：

  ```sh
  # private pkcs1/pkcs8
  # openssl rsa -in private_pkcs1.pem -text -noout
  # openssl rsa -in private_pkcs8.pem -text -noout
  openssl rsa -in ${private_pkcs1or8.pem} -text -noout

  # public pkcs8(not support pkcs1)
  # openssl rsa -in public_pkcs8.pem -text -noout -pubin
  openssl rsa -in ${public_pkcs8.pem} -text -noout -pubin
  ```

- 生成 RSA 的 private key：

  ```sh
  # generate PKCS #1
  # openssl genrsa -out private_pkcs1.pem 2048
  openssl genrsa -out ${private_pkcs1.pem} ${bits}

  # generate encrypted private key PKCS #1
  # openssl genrsa -des3 -out encrypted_private_pkcs1.pem 2048
  openssl genrsa -des3 -out ${encrypted_private_pkcs1.pem} ${bits}


  # generate private key PKCS #8
  # openssl genpkey -algorithm RSA -out private_pkcs8.pem 2048
  openssl genpkey -algorithm RSA -out ${private_pkcs8.pem} ${bits}

  # generate encrypted private key PKCS #8
  # openssl genpkey -des3 -algorithm RSA -out encrypted_private_pkcs8.pem 2048
  openssl genpkey -des3 -algorithm RSA -out ${encrypted_private_pkcs8.pem} ${bits}
  ```

- 从 private key 提取 public key：

  ```sh
  # private pkcs1 ---> public pkcs1
  # openssl rsa -in private_pkcs1.pem -out public_pkcs1.pem -pubout -RSAPublicKey_out
  openssl rsa -in ${private_pkcs1.pem} -out ${public_pkcs1.pem} -pubout -RSAPublicKey_out

  # private pkcs8 ---> public pkcs8
  # openssl rsa -in private_pkcs8.pem -out public_pkcs1.pem -pubout -RSAPublicKey_out
  openssl rsa -in ${private_pkcs8.pem} -out ${public_pkcs1.pem} -pubout -RSAPublicKey_out

  # private pkcs1 ---> public pkcs8
  # openssl rsa -in private_pkcs1.pem -out public_pkcs8.pem -pubout
  openssl rsa -in ${private_pkcs1.pem} -out ${public_pkcs8.pem} -pubout

  # private pkcs8 ---> public pkcs1
  # openssl rsa -in private_pkcs8.pem -out public_pkcs8.pem -pubout
  openssl rsa -in ${private_pkcs8.pem} -out ${public_pkcs8.pem} -pubout
  ```

- RSA public key 格式转换：

  ```sh
  # public pkcs8 ---> public pkcs1
  # openssl rsa -in public_pkcs8.pem -out public_pkcs1.pem -pubin -RSAPublicKey_out
  openssl rsa -in ${public_pkcs8_pem} -out ${public_pkcs1_pem} -pubin -RSAPublicKey_out

  # public pkcs8 ---> public pkcs1
  # openssl rsa -in public_pkcs8.pem -out public_pkcs1.pem -pubin -RSAPublicKey_out
  openssl rsa -in ${public_pkcs8_pem} -out ${public_pkcs1_pem} -pubin -RSAPublicKey_out
  ```

- RSA private key 格式转换：

  ```sh
  # private pkcs1 ---> private pkcs8
  # openssl pkcs8 -in private_pkcs1.pem -out private_pkcs8.pem -topk8 -nocrypt
  openssl pkcs8 -in ${private_pkcs1.pem} -out ${private_pkcs8.pem} -topk8 -nocrypt

  # private pkcs8 --> private pkcs1
  # openssl rsa -in private_pkcs8.pem -out private_pkcs1.pem
  openssl rsa -in ${private_pkcs8.pem} -out ${private_pkcs1.pem}
  ```

## PEM 与 ne 转换

实际场景中，对于 RSA 公钥并非仅仅需要 RSA Public Key PEM，而是需要获得 Base64 encode 格式的 RSA n 和 e。并且往往也需要 RSA n 和 e 转换 RSA Public Key PEM（因为不少第三方库都直接依赖的 RSA Public Key PEM 而非 n 和 e）。

例如 JWT 中通过 jku 暴露 JWKs，其中 RS256 算法（基于 RSA 的数字签名）的 n 和 e 是 Base64 格式的：

```
{
    "keys": [{
        "kty":"EC",
        "crv":"P-256",
        "x":"MKBCTNIcKUSDii11ySs3526iDZ8AiTo7Tu6KPAqv7D4",
        "y":"4Etl6SRW2YiLUrN5vfvVHuhp7x8PxltmWWlbbM4IFyM",
        "use":"enc",
        "kid":"1"
    },{
        "kty":"RSA",
        "n": "0vx7agoebGcQSuuPiLJXZptN9nndrQmbXEps2aiAFbWhM78LhWx4cbbfAAtVT86zwu1RK7aPFFxuhDR1L6tSoc_BJECPebWKRXjBZCiFV4n3oknjhMstn64tZ_2W-5JsGY4Hc5n9yBXArwl93lqt7_RN5w6Cf0h4QyQ5v-65YGjQR0_FDW2QvzqY368QQMicAtaSqzs8KJZgnYb9c7d0zgdAZHzu6qMQvRL5hajrn1n91CbOpbISD08qNLyrdkt-bFTWhAI4vMQFh6WeZu0fM4lFd2NcRwr3XPksINHaQ-G_xBniIqbw0Ls1jF44-csFCur-kEgU8awapJzKnqDKgw",
        "e":"AQAB",
        "alg":"RS256",
        "kid":"2011-04-29"
    }]
}
```

- [tests](tests.md) 提供了 PEM 和 JWK RS256 密钥转换示例。


## 参考文献

1. [RFC 3447(PKCS #1)](https://tools.ietf.org/html/rfc3447)
1. [RFC 5208(PKCS #8)](https://tools.ietf.org/html/rfc5208)
1. [RFC 7468(Textual Encodings of PKIX, PKCS, and CMS Structures)](https://tools.ietf.org/html/rfc7468)
1. [PEM Wiki](https://en.wikipedia.org/wiki/Privacy-Enhanced_Mail)
1. [ASN.1 Wiki](https://en.wikipedia.org/wiki/ASN.1)
1. [PKCS Wiki](https://en.wikipedia.org/wiki/PKCS)
1. [X.690 Wiki](https://en.wikipedia.org/wiki/X.690)
1. [DER Wiki](https://en.wikipedia.org/wiki/X.690#DER_encoding)
1. [Extract from Abstract Syntax Notation One (ASN.1) ](https://www.bgbm.org/TDWG/acc/Documents/asn1gloss.htm)
1. [ASN.1 key structures in DER and PEM](https://tls.mbed.org/kb/cryptography/asn1-key-structures-in-der-and-pem)
1. [公钥密码学标准](https://zh.wikipedia.org/wiki/%E5%85%AC%E9%92%A5%E5%AF%86%E7%A0%81%E5%AD%A6%E6%A0%87%E5%87%86)
1. [ASN.1 key structures in DER and PEM](https://tls.mbed.org/kb/cryptography/asn1-key-structures-in-der-and-pem)
1. [RSA 算法原理（一）](http://www.ruanyifeng.com/blog/2013/06/rsa_algorithm_part_one.html)
1. [RSA 算法原理（二）](http://www.ruanyifeng.com/blog/2013/07/rsa_algorithm_part_two.html)
1. [加密解密-RSA](https://www.shangyang.me/categories/%E8%AE%A1%E7%AE%97%E6%9C%BA%E7%A7%91%E5%AD%A6%E4%B8%8E%E6%8A%80%E6%9C%AF/%E5%8A%A0%E5%AF%86%E8%A7%A3%E5%AF%86/RSA/)
1. [RSA 密钥格式解析](https://www.jianshu.com/p/c93a993f8997)
1. [PEM, DER, CRT, and CER: X.509 Encodings and Conversions](https://www.ssl.com/guide/pem-der-crt-and-cer-x-509-encodings-and-conversions/)
