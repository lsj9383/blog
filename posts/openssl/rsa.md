# Openssl RSA

<!-- TOC -->

- [Openssl RSA](#openssl-rsa)
    - [概览](#概览)
    - [RSA 原理](#rsa-原理)
    - [密钥编码](#密钥编码)
        - [ASN.1](#asn1)
        - [DER](#der)
        - [PKCS](#pkcs)
        - [PEM](#pem)
    - [Openssl 命令](#openssl-命令)
    - [参考文献](#参考文献)

<!-- /TOC -->

## 概览

本文主要记录了 RSA 基本知识、存储和传输格式以及 Openssl RSA 命令（后续如果有时间会补充 Openssl RSA 编程），以便快速查阅和回顾。

## RSA 原理

## 密钥编码

通过对密钥进行编码，可以方便密钥的存储和传输，并为了让不同系统以统一的方式去解析密钥，对此编码方式进行了标准化。

RSA 的密钥的编码会涉及到以下标准：

- [ASN.1](#asn1) 用于定义和描述独立于特定计算机硬件的对象结构。属于 [X.680](https://www.itu.int/rec/T-REC-X.680) 标准。
- [DER](#der) 用于将 ASN.1 描述的对象编码为具体的数据流规则。是 [X.690](https://www.itu.int/rec/T-REC-X.690/) 标准的一部分。
- [PKCS](#pkcs) 公钥密码学标准，由多个部分组成。对于 RSA，我们需要关心的是 PKCS #1 和 PKCS #8：
  - PKCS #1，通过 ASN.1 定义的 RSA 公钥和私钥的格式。
  - PKCS #8，通过 ASN.1 定义的 通用密钥格式。相比于 #1 仅用于 RSA，#8 可以用于多种密码学算法的密钥。
- [PEM](#pem) 为了方便 ASCII 系统中传输和存储密钥而定义的一种格式化标准。

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

### PKCS

公钥密码学标准（Public Key Cryptography Standards, PKCS）。

虽然 PKCS 这里名称指的是 “公钥”，但实际上 PKCS 同时规定了公钥和私钥。

**注意：**

- 为了保障 RSA 公钥的安全性，还需要[公钥基础设施](https://en.wikipedia.org/wiki/Public_key_infrastructure)（Public key infrastructure, PKI）。

### PEM

若已有 PEM 文件，则可以通过 <http://phpseclib.sourceforge.net/x509/asn1parse.php> 以 ASN.1 格式打印。

**注意：**

- PKCS #8 的数据可能经过加密，无法通过 asn1parse.php 直接解析得到。

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
  # openssl genrsa -out private_pkcs1.pem 2048
  openssl genrsa -out ${private_pkcs1.pem} ${bits}
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

## 参考文献

1. [RFC 3447(PKCS #1)](https://tools.ietf.org/html/rfc3447)
1. [RFC 5208(PKCS #8)](https://tools.ietf.org/html/rfc5208)
1. [PEM Wiki](https://en.wikipedia.org/wiki/Privacy-Enhanced_Mail)
1. [ASN.1 Wiki](https://en.wikipedia.org/wiki/ASN.1)
1. [PKCS Wiki](https://en.wikipedia.org/wiki/PKCS)
1. [X.690 Wiki](https://en.wikipedia.org/wiki/X.690)
1. [DER Wiki](https://en.wikipedia.org/wiki/X.690#DER_encoding)
1. [Extract from Abstract Syntax Notation One (ASN.1) ](https://www.bgbm.org/TDWG/acc/Documents/asn1gloss.htm)
1. [ASN.1 key structures in DER and PEM](https://tls.mbed.org/kb/cryptography/asn1-key-structures-in-der-and-pem)
1. [公钥密码学标准](https://zh.wikipedia.org/wiki/%E5%85%AC%E9%92%A5%E5%AF%86%E7%A0%81%E5%AD%A6%E6%A0%87%E5%87%86)
1. [RSA 算法原理（一）](http://www.ruanyifeng.com/blog/2013/06/rsa_algorithm_part_one.html)
1. [RSA 算法原理（二）](http://www.ruanyifeng.com/blog/2013/07/rsa_algorithm_part_two.html)
1. [加密解密-RSA](https://www.shangyang.me/categories/%E8%AE%A1%E7%AE%97%E6%9C%BA%E7%A7%91%E5%AD%A6%E4%B8%8E%E6%8A%80%E6%9C%AF/%E5%8A%A0%E5%AF%86%E8%A7%A3%E5%AF%86/RSA/)
1. [RSA 密钥格式解析](https://www.jianshu.com/p/c93a993f8997)
