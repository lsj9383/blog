# Openssl RSA

<!-- TOC -->

- [Openssl RSA](#openssl-rsa)
    - [概览](#概览)
    - [RSA 原理](#rsa-原理)
    - [密钥编码](#密钥编码)
        - [PKCS](#pkcs)
        - [PEM](#pem)
    - [Openssl 命令](#openssl-命令)
    - [参考文献](#参考文献)

<!-- /TOC -->

## 概览

笔者在 Nginx 支持 RS256 的 JWT 统一校验时涉及到了 RSA 相关基础知识，进而学习并整理了本文。

本文主要记录了 RSA 相关的基础知识、存储和传输格式以及 Openssl 的 RSA 命令（后续如果有时间会补充 Openssl 的 RSA 编程），以便快速查阅和回顾。

## RSA 原理

## 密钥编码

通过对密钥进行编码，可以方便密钥的存储和传输，并为了让不同系统以统一的方式去解析密钥，对此编码方式进行了标准化，即`公钥密码学标准`（Public Key Cryptography Standards, PKCS）。

PKCS 是以二进制格式保持的密钥，为了更方便的查看文件，会将 PKCS 进行 base64，进而得到 PEM 文件。

**注意：**

- 为了保障 RSA 公钥的安全性，还需要[公钥基础设施](https://en.wikipedia.org/wiki/Public_key_infrastructure)（Public key infrastructure, PKI）。

### PKCS

公钥密码学标准（Public Key Cryptography Standards, PKCS）。

> RSA信息安全公司旗下的RSA实验室为了发扬公开密钥技术的使用，便发展了一系列的公开密钥密码编译标准。只不过，虽然该标准具有相当大的象征性，也被信息界的产业所认同；但是，若RSA公司认为有必要，这些标准的内容仍然可能会更动。

虽然 PKCS 这里名称指的是 “公钥”，但实际上 PKCS 同时规定了公钥和私钥。

### PEM

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

1. [ASN.1 key structures in DER and PEM](https://tls.mbed.org/kb/cryptography/asn1-key-structures-in-der-and-pem)
1. [PKCS Wiki](https://en.wikipedia.org/wiki/PKCS)
1. [公钥密码学标准](https://zh.wikipedia.org/wiki/%E5%85%AC%E9%92%A5%E5%AF%86%E7%A0%81%E5%AD%A6%E6%A0%87%E5%87%86)
1. [RSA 算法原理（一）](http://www.ruanyifeng.com/blog/2013/06/rsa_algorithm_part_one.html)
1. [RSA 算法原理（二）](http://www.ruanyifeng.com/blog/2013/07/rsa_algorithm_part_two.html)
1. [加密解密-RSA](https://www.shangyang.me/categories/%E8%AE%A1%E7%AE%97%E6%9C%BA%E7%A7%91%E5%AD%A6%E4%B8%8E%E6%8A%80%E6%9C%AF/%E5%8A%A0%E5%AF%86%E8%A7%A3%E5%AF%86/RSA/)
1. [RSA 密钥格式解析](https://www.jianshu.com/p/c93a993f8997)
