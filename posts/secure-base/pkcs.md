# PKCS

[TOC]

## 概览

什么是 PKCS？

> In cryptography, PKCS stands for "Public Key Cryptography Standards".

PKCS 是由 RSA Security LLC（美国 RSA 数据安全公司及其合作伙伴）制定的一组公钥密码学标准。

虽然 PKCS 并非行业标准，但近年来运用的非常广，其中部分已经进入了 RFC。

下表参考：[Wiki PKCS](https://en.wikipedia.org/wiki/PKCS)。

PKCS 标准 | 版本 | 名称 | 描述
-|-|-|-
PKCS #1 | 2.2 | RSA 密码算法标准 | 已进入 RFC 8017。义 RSA 公钥和私钥的数学属性和格式，以及用于执行 RSA 加密、解密以及生成和验证签名的基本算法和编码。
PKCS #2 | - | 已撤销 | 自 2010 年废弃。涵盖消息摘要的 RSA 加密；随后合并到 PKCS #1。
PKCS #3 | 1.4 | DH 密钥协商标准 |
PKCS #4 | - | 已撤销 | 自 2010 年废弃。涵盖的 RSA 密钥语法；随后合并到 PKCS #1。
PKCS #5 | 2.1 | 基于密码的加密标准 | 已进入 RFC 8018。
PKCS #6 | 1.5 | 扩展证书语法标准
PKCS #7 | 1.5 | 加密消息语法标准 | 已进入 RFC 2315。
PKCS #8 | 1.2 | 私钥信息语法标准 | 已进入 RFC 5208。
PKCS #9 | 2.0 | 选定的属性类型 | 已进入 RFC 2985。
PKCS #10 | 1.7 | | 已进入 RFC 2986。
PKCS #11 | 3.0
PKCS #12 | 1.1 | | 已进入 RFC 7292。
PKCS #13 | - | 椭圆曲线密码学标准 | 已放弃，仅参考 1998 年的提案。
PKCS #14 | - | 伪随机数生成 | 已放弃，没有文件存在。
PKCS #15 | 1.1 | 加密令牌信息格式标准


## PKCS #7

## PKCS #8

标准化请参考 [RFC 5208](https://www.rfc-editor.org/rfc/rfc5208)。

该标准描述了私钥信息的语法，包括两种描述方式：

- 公钥算法所用的私钥以及相关属性。
- 基于口令进行加密的私钥信息。

### 私钥信息语法（Private-Key Information Syntax）

这部分给出了私钥信息语法：

```asn
PrivateKeyInfo ::= SEQUENCE {
    version                   Version,
    privateKeyAlgorithm       PrivateKeyAlgorithmIdentifier,
    privateKey                PrivateKey,
    attributes           [0]  IMPLICIT Attributes OPTIONAL
}

Version ::= INTEGER

PrivateKeyAlgorithmIdentifier ::= AlgorithmIdentifier

PrivateKey ::= OCTET STRING

Attributes ::= SET OF Attribute
```

PrivateKeyInfo 中的字段含义如下：

字段 | 含义
-|-
version | 语法（指的 PKCS #8 定义的语法版本）版本号，以便与本文档的未来版本兼容。当前固定为 0。
privateKeyAlgorithm | 标识私钥算法。该标识取自 PKCS #1 中的定义。
privateKey | 其内容是私钥的值。对私钥内容的解释是在私钥算法中定义的，例如对于 RSA 私钥，其内容类型是 RSAPrivateKey 的值的 BER 编码。
attributes | 一组可扩展属性。

### 加密的私钥信息语法（Encrypted Private-Key Information Syntax）

```asn
EncryptedPrivateKeyInfo ::= SEQUENCE {
    encryptionAlgorithm  EncryptionAlgorithmIdentifier,
    encryptedData        EncryptedData
}

EncryptionAlgorithmIdentifier ::= AlgorithmIdentifier

EncryptedData ::= OCTET STRING
```

EncryptedPrivateKeyInfo 中的字段含义如下：

字段 | 含义
-|-
encryptionAlgorithm | 标识私钥信息的加密算法，定义在 PKCS #5 中，例如 pbeWithMD2AndDES-CBC 或 pbeWithMD5AndDES-CBC。
encryptedData | 是私钥信息的密文。

加密流程如下：

1. 先对 Private-Key Information 进行 BER 编码，得到一个字节数组。
1. 对上面的字节数组使用密钥加密，得到另一个字节数组，即加密过程。

### PKCS #8 与 OpenSSL

OpenSSL 默认生成的私钥 PEM 一般标识 PKCS #8 的，要使用 PKCS #8 进行存储需要进行转换：

```sh
# 随便生成一个 PKCS #1 的 RSA 私钥
$ openssl genrsa -out private.pem 1024

# 转为 PKCS #8（对于 EC 的私钥也是通用的）
$ openssl pkcs8 -topk8 -inform PEM -in private.pem -outform pem -nocrypt -out pkcs8.pem

# 转为 PKCS #1（pkcs1.pem 和 private.pem 应该是相同的）
$ openssl rsa -in pkcs8.pem -out pkcs1.pem
```

## PKCS #12

## 附录：私钥信息的结构定义

该附录罗列出不同非对称算法，使用的私钥信息结构。

### RSA privateKey 结构

请参考：[PKCS #1 RSA Private Key Syntax](https://www.rfc-editor.org/rfc/rfc8017#appendix-A.1.2)。

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

OpenSSL 生成该结构私钥文件：

```sh
# 生成公私钥
$ genrsa -out rsa_private_key.pem 1024
# 使用 -RSAPublicKey_out 时，会使用 PKCS#1 的公钥 ASN.1 语法格式，否则使用 RFC5280 的 SubjectPublicKeyInfo 格式
$ openssl rsa -in rsa_private_key.pem -pubout -out rsa_public_key.pem -RSAPublicKey_out

# 解析私钥的 ASN.1 格式：
$ openssl asn1parse -inform PEM -in rsa_private_key.pem 
    0:d=0  hl=4 l= 605 cons: SEQUENCE          
    4:d=1  hl=2 l=   1 prim: INTEGER           :00
    7:d=1  hl=3 l= 129 prim: INTEGER           :D065C7A7B8E40058484A045D423DEEA04720014B4342D55ABB8628C321578E5EC92AC2C04C2B787408214EA9A84C8A6902E63CCB64284D34355402E6EA372BE59D1DF37A7CB3FB191A9928C6D2C30B82FBC300EADC37B44803E801953FEE08356D3E9333509E9F58E8E7294BEC88920039D34F846FF7D9F95F9E5C250C006755
  139:d=1  hl=2 l=   3 prim: INTEGER           :010001
  144:d=1  hl=3 l= 128 prim: INTEGER           :6907C2F66F22CA61B41D49D1CEBEF3F367A563C190E6B02D0871F73D512295A883EEBF34B7AEF90851C8A7A2AE25D5645387C28027BC801C9DFBF77275FCD46BFD6BEC9059286E936B3AA44FF80D73D7B3598D8FF0D61615DE4930D25D9913938C9D1F69CC3CBE101561CCC89621E1CC3CCE0F957C529BDFDA2D7A3B25BD5409
  275:d=1  hl=2 l=  65 prim: INTEGER           :FC0C3A95D3F3BAA8177781A6648530AE35857CC4C69EFE86CC75632D8E52265ED23348EFA83C9CEF12995CA67399D6D2A35C8CBDA42ED71A2632D5EF1EF365FF
  342:d=1  hl=2 l=  65 prim: INTEGER           :D3AA548D7FB6B08BD8989894FAF30041DC914ED04474BD8960FF73EB8AE43F5DE9B4EEF8AE8C4F3AF36281EDA362E58AA2CCE9A81EC2FAD2C6CB7CF798B0BAAB
  409:d=1  hl=2 l=  65 prim: INTEGER           :C73F6390CDDCFED1A2BB766273545707608805FA0889E7EBE7F56451BF107204C3668761ED3CFD5281017B9C9A06232CA0B7A90AC19FC5AB8646E997FE7FAB41
  476:d=1  hl=2 l=  65 prim: INTEGER           :C65A3D4828A1A40A395CAEC815EF38937FC62FEC5DEA645FE4251F9560A00A7DD06FFCEDD06CAE26D943BBEC5D0B657E28980C72BEF90B2210A74AA1A0562567
  543:d=1  hl=2 l=  64 prim: INTEGER           :46959102693BC841E96C4CC19C25F44C713FED68C89E00B08FC0DEAC9888CD67340EBA0E6F924F7A5A538D6BE5AA2D8C5F9A4729DE1006CC546CE714019018DB

# 解析公钥的 ASN.1 格式（PKCS #1 语法的公钥）
$ openssl asn1parse -inform PEM -in rsa_public_key.pem
    0:d=0  hl=3 l= 137 cons: SEQUENCE          
    3:d=1  hl=3 l= 129 prim: INTEGER           :D065C7A7B8E40058484A045D423DEEA04720014B4342D55ABB8628C321578E5EC92AC2C04C2B787408214EA9A84C8A6902E63CCB64284D34355402E6EA372BE59D1DF37A7CB3FB191A9928C6D2C30B82FBC300EADC37B44803E801953FEE08356D3E9333509E9F58E8E7294BEC88920039D34F846FF7D9F95F9E5C250C006755
  135:d=1  hl=2 l=   3 prim: INTEGER           :010001
```

### EC privateKey 结构

请参考：[Elliptic Curve Private Key Structure(RFC 5919)](https://www.rfc-editor.org/rfc/rfc5915)。

```asn
ECPrivateKey ::= SEQUENCE {
    version        INTEGER { ecPrivkeyVer1(1) } (ecPrivkeyVer1),
    privateKey     OCTET STRING,
    parameters [0] ECParameters {{ NamedCurve }} OPTIONAL,
    publicKey  [1] BIT STRING OPTIONAL
}
```

ECPrivateKey 中的各字段含义：

字段 | 含义
-|-
version | 椭圆曲线私钥结构的语法版本号。对于此版本的文档，应将其设置为 ecPrivkeyVer1，值为 1。
privateKey | 椭圆曲线的私钥裸数据。
parameters | 指定与私钥关联的椭圆曲线域参数。namedCurve 是一个对象标识符（例如 sm2、prime256v1 等），它完全标识一组特定椭圆曲线域参数的所需值。
publicKey | 私钥相关联的椭圆曲线公钥。


**注意：**

- 对于 parameters 字段，尽管 ASN.1 表明参数字段是可选的，但符合本文档的实现必须始终包含参数字段。
- 对于 publicKey 字段，尽管 ASN.1 表明该字段是可选的，但符合本文档的实现应该总是包含 publicKey 字段。
  - 当公钥已经通过其他机制分发时，可以省略 publicKey 字段，这超出了本文档的范围。
  - 给定私钥和参数，公钥总是可以重新计算；该字段的存在是为了方便消费者。

OpenSSL 生成该结构的 PEM 私钥文件：

```sh
# OpenSSL ecparam 的生成默认就是符合 RFC 5919 标准的
$ openssl ecparam -name prime256v1 -genkey -noout -out ecprivate.key

$ openssl asn1parse -inform PEM -in ecprivate.key
    0:d=0  hl=2 l= 119 cons: SEQUENCE          
    2:d=1  hl=2 l=   1 prim: INTEGER           :01
    5:d=1  hl=2 l=  32 prim: OCTET STRING      [HEX DUMP]:BBBA5B99A5D3CBF5F514C8B213290E427E760EDA7E174F0EE044B2DC8067FDFC
   39:d=1  hl=2 l=  10 cons: cont [ 0 ]        
   41:d=2  hl=2 l=   8 prim: OBJECT            :prime256v1
   51:d=1  hl=2 l=  68 cons: cont [ 1 ]        
   53:d=2  hl=2 l=  66 prim: BIT STRING

# 最后的 66 prim: BIT STRING 是公钥，可以通过 -dump 打印出来：
$ openssl asn1parse -inform PEM -in ecprivate.key -dump
    0:d=0  hl=2 l= 119 cons: SEQUENCE          
    2:d=1  hl=2 l=   1 prim: INTEGER           :01
    5:d=1  hl=2 l=  32 prim: OCTET STRING      
      0000 - bb ba 5b 99 a5 d3 cb f5-f5 14 c8 b2 13 29 0e 42   ..[..........).B
      0010 - 7e 76 0e da 7e 17 4f 0e-e0 44 b2 dc 80 67 fd fc   ~v..~.O..D...g..
   39:d=1  hl=2 l=  10 cons: cont [ 0 ]        
   41:d=2  hl=2 l=   8 prim: OBJECT            :prime256v1
   51:d=1  hl=2 l=  68 cons: cont [ 1 ]        
   53:d=2  hl=2 l=  66 prim: BIT STRING        
      0000 - 00 04 e4 51 b8 03 ea 1b-0d f6 1e 12 74 48 92 10   ...Q........tH..
      0010 - eb b0 e3 16 bb 78 85 f1-9b 8b 24 36 3b 95 7a 05   .....x....$6;.z.
      0020 - a8 4c 54 67 9d 1e 66 86-f7 ea 86 98 7d 88 85 03   .LTg..f.....}...
      0030 - 7e 7c b7 e8 f4 a5 b2 f3-36 89 34 00 8a 32 6c 66   ~|......6.4..2lf
      0040 - 01 7f
```

## 附录：参考文献

1. [写给工程师：关于证书（certificate）和公钥基础设施（PKI）的一切](http://arthurchiao.art/blog/everything-about-pki-zh/)
1. [OpenSSL 1.1.1 手册](https://www.openssl.org/docs/man1.1.1/man1/)
1. [Wiki PKCS](https://en.wikipedia.org/wiki/PKCS)
1. [PKCS #8(RFC 5208)](https://www.rfc-editor.org/rfc/rfc5208)
1. [Elliptic Curve Private Key Structure(RFC 5919)](https://www.rfc-editor.org/rfc/rfc5915)
1. [Elliptic Curve Cryptography Subject Public Key Information(RFC 5480)](https://www.rfc-editor.org/rfc/rfc5480)
1. [How can I transform between the two styles of public key format, one "BEGIN RSA PUBLIC KEY", the other is "BEGIN PUBLIC KEY"](https://stackoverflow.com/questions/18039401/how-can-i-transform-between-the-two-styles-of-public-key-format-one-begin-rsa)
